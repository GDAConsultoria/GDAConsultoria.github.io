import os
import shutil
import urllib.parse
from bs4 import BeautifulSoup

# Paths
INPUT_FOLDER = "062c921f-fed7-4da7-87b7-e0736cad417e_Export-90b6bcb0-12ae-4ea7-908d-2192e732d8fc"
TEMPLATE_PATH = "SumModuleSample1.html"
OUTPUT_FOLDER = "generated_submodules"
IMAGES_FOLDER = "generated_submodules/images"

# Ensure output directories exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# Load your base template
with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    base_template = f.read()

# Traverse subfolders of INPUT_FOLDER
for root, dirs, files in os.walk(INPUT_FOLDER):
    for filename in files:
        if not filename.endswith(".html"):
            continue

        module_name = os.path.splitext(filename)[0]
        input_path = os.path.join(root, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"Submodule_{module_name}.html")

        # Parse HTML content
        with open(input_path, "r", encoding="utf-8") as f:
            data_soup = BeautifulSoup(f, "html.parser")

        # Extract title and goal
        title_tag = data_soup.find("h1", class_="page-title")
        title = title_tag.get_text(strip=True) if title_tag else module_name

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

                # Locate image relative to the HTML file's folder
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

        heading = template_soup.find("h1", class_="head")
        if heading:
            heading.string = title

        goal_p = template_soup.select_one(".goal_container p")
        if goal_p:
            goal_p.string = f"Objetivo: {goal_text}"

        steps_container = template_soup.find("div", class_="steps_container")
        if steps_container:
            steps_container.clear()

            for i, step in enumerate(steps, start=1):
                step_div = template_soup.new_tag("div", **{"class": "step", "id": f"step{i}"})
                p = template_soup.new_tag("p")
                p.string = f"{i}. {step['title']}"
                step_div.append(p)

                ul = template_soup.new_tag("ul")
                for line in step["text"].strip().split("\n"):
                    li = template_soup.new_tag("li")
                    li.string = line.strip()
                    ul.append(li)
                step_div.append(ul)
                steps_container.append(step_div)

                if step["img"]:
                    span = template_soup.new_tag("span", **{"class": "screenshot", "id": f"screenshot-{i}"})
                    img = template_soup.new_tag("img", src=step["img"], alt="Screenshot")
                    span.append(img)
                    steps_container.append(span)

        # Save result
        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(str(template_soup))

        print(f"✔ Generated: {output_path}")
