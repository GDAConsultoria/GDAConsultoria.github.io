import os
import shutil
import urllib.parse
from bs4 import BeautifulSoup

# Paths
INPUT_FOLDER = "062c921f-fed7-4da7-87b7-e0736cad417e_Export-90b6bcb0-12ae-4ea7-908d-2192e732d8fc"
TEMPLATE_PATH = "SubModuleSample.html"
OUTPUT_FOLDER = "generated_submodules"
IMAGES_FOLDER = os.path.join(OUTPUT_FOLDER, "images")

# Ensure output directories exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# Load your base template
with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    base_template = f.read()

# Store titles and file names for index generation
generated_pages = []

# Traverse subfolders of INPUT_FOLDER
for root, dirs, files in os.walk(INPUT_FOLDER):
    for filename in files:
        if not filename.endswith(".html"):
            continue

        module_name = os.path.splitext(filename)[0]
        input_path = os.path.join(root, filename)

        # Parse HTML content
        with open(input_path, "r", encoding="utf-8") as f:
            data_soup = BeautifulSoup(f, "html.parser")

        # Extract title and goal
        title_tag = data_soup.find("h1", class_="page-title")
        title = title_tag.get_text(strip=True) if title_tag else module_name
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title).strip()
        output_filename = f"{safe_title}.html"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        goal_div = data_soup.find("div", class_="callout")
        goal_text = goal_div.get_text(strip=True) if goal_div else "No goal found."

        # Extract steps
        steps = []
        details_tags = data_soup.find_all("details")
        for idx, detail in enumerate(details_tags, start=1):
            summary = detail.find("summary")
            step_title = summary.get_text(strip=True) if summary else f"Step {idx}"

            text_blocks = detail.find_all(["p", "li"])
            step_text = "\n".join(p.get_text(strip=True) for p in text_blocks if p.get_text(strip=True))

            img_tag = detail.find("img")
            img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

            # Correct image path
            if img_src and not img_src.startswith("http"):
                decoded_src = urllib.parse.unquote(img_src)
                img_filename = os.path.basename(decoded_src)

                html_folder = os.path.dirname(input_path)
                src_img_path = os.path.join(html_folder, img_filename)
                dest_img_path = os.path.join(IMAGES_FOLDER, img_filename)

                if os.path.exists(src_img_path):
                    shutil.copy2(src_img_path, dest_img_path)
                    img_src = os.path.join("images", img_filename)
                else:
                    print(f"⚠️ Image not found: {src_img_path}")
                    img_src = None

            steps.append({
                "title": step_title,
                "text": step_text,
                "img": img_src
            })

        # Inject data into template
        template_soup = BeautifulSoup(base_template, "html.parser")

        head_div = template_soup.find("div", class_="head")
        if head_div:
            span_tag = head_div.find("span")
            if span_tag:
                span_tag.string = title

        goal_alert = template_soup.select_one("div.alert-info strong")
        if goal_alert:
            goal_alert.next_sibling.replace_with(f" {goal_text}")

        accordion = template_soup.find("div", {"id": "accordionSteps"})
        if accordion:
            accordion.clear()

            for i, step in enumerate(steps, start=1):
                acc_item = template_soup.new_tag("div", **{"class": "accordion-item"})

                h2 = template_soup.new_tag("h2", **{"class": "accordion-header", "id": f"heading{i}"})
                button = template_soup.new_tag("button", **{
                    "class": "accordion-button collapsed",
                    "type": "button",
                    "data-bs-toggle": "collapse",
                    "data-bs-target": f"#collapse{i}"
                })
                button.string = f"Step {i}: {step['title']}"
                h2.append(button)
                acc_item.append(h2)

                collapse_div = template_soup.new_tag("div", **{
                    "id": f"collapse{i}",
                    "class": "accordion-collapse collapse"
                })
                body_div = template_soup.new_tag("div", **{"class": "accordion-body"})

                ul = template_soup.new_tag("ul")
                for line in step["text"].split("\n"):
                    li = template_soup.new_tag("li")
                    li.string = line
                    ul.append(li)
                body_div.append(ul)

                if step["img"]:
                    img = template_soup.new_tag("img", src=step["img"], **{
                        "class": "img-fluid rounded mb-3",
                        "alt": "Screenshot"
                    })
                    body_div.append(img)

                body_div.append(template_soup.new_tag("div"))

                collapse_div.append(body_div)
                acc_item.append(collapse_div)

                accordion.append(acc_item)

        # Save result
        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(str(template_soup))

        generated_pages.append((title, output_filename))
        print(f"✔ Generated: {output_path}")

# Generate Table of Contents page
index_path = os.path.join(OUTPUT_FOLDER, "index.html")
toc_html = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>SAP TRM Training Modules</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 2rem;
            background: #f9f9f9;
            color: #333;
        }
        h1 {
            text-align: center;
            margin-bottom: 2rem;
        }
        ul {
            list-style: none;
            padding: 0;
        }
        li {
            margin: 1rem 0;
        }
        a {
            text-decoration: none;
            font-weight: bold;
            color: #2c3e50;
        }
        a:hover {
            color: #007acc;
        }
    </style>
</head>
<body>
    <h1>SAP TRM Training Modules</h1>
    <ul>
"""

for title, filename in generated_pages:
    toc_html += f'        <li><a href="{filename}">{title}</a></li>\n'

toc_html += """
    </ul>
</body>
</html>
"""

with open(index_path, "w", encoding="utf-8") as f:
    f.write(toc_html)

print(f"📘 Table of Contents generated: {index_path}")