import os
import json
import streamlit as st

# Define the function that combines the COCO JSON files
def combine_coco_jsons(coco_json_list):
    if not coco_json_list:
        # If the list is empty, return an empty dictionary
        return {}
    combined_json = coco_json_list[0]
    taken_ids = [i['id'] for i in combined_json['images']]
    for idx in range(len(combined_json['annotations'])):
        combined_json['annotations'][idx]['id'] = idx + 1
    annotation_id = max(i['id'] for i in combined_json['annotations']) + 1
    for coco_json in coco_json_list[1:]:
        temp_id_dict = {}
        for image in coco_json['images']:
            new_id = image['id']
            while new_id in taken_ids:
                new_id += 1
            taken_ids.append(new_id)
            temp_id_dict[image['id']] = new_id
            image['id'] = new_id
            combined_json['images'].append(image)
        for annotation in coco_json['annotations']:
            #print(annotation_id)
            annotation['id'] = annotation_id
            annotation['image_id'] = temp_id_dict[annotation['image_id']]
            combined_json['annotations'].append(annotation)
            annotation_id += 1
        if 'categories' in coco_json:
            if 'categories' not in combined_json:
                combined_json['categories'] = []
            for category in coco_json['categories']:
                if category not in combined_json['categories']:
                    combined_json['categories'].append(category)
    if 'categories' not in combined_json:
        combined_json['categories'] = []
    return combined_json

# Define the Streamlit app
def app():
    st.title("Hyundai JSON Merger")

    # Create a folder uploader
    uploaded_folder = st.file_uploader("Choose a folder of JSON files", type=["json"], accept_multiple_files=True)

    if uploaded_folder is not None:
        # Create a temporary directory to save the uploaded files
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Save the uploaded files to the temporary directory
        for uploaded_file in uploaded_folder:
            with open(os.path.join(temp_dir, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())

        # Combine the COCO JSON files
        coco_json_list = [os.path.join(temp_dir, i) for i in os.listdir(temp_dir) if i.endswith('.json')]
        combined = combine_coco_jsons([json.load(open(i)) for i in coco_json_list])

        # Fix the combined data for the given use case
        crowd_cat = [i['id'] for i in combined['categories'] if i['name'].lower() == 'crowd'][0]
        ignore_cat = [i['id'] for i in combined['categories'] if i['name'].lower() == 'ignore'][0]
        person_cat = [i['id'] for i in combined['categories'] if i['name'].lower() == 'person'][0]
        new_ann = []
        for ann in combined['annotations']:
            if ann['category_id'] == crowd_cat:
                ann['category_id'] = 1
                ann['iscrowd'] = 1
                ann['ignore'] = 1
                new_ann.append(ann)
            elif ann['category_id'] == ignore_cat:
                ann['category_id'] = 1
                ann['iscrowd'] = 0
                ann['ignore'] = 1
                new_ann.append(ann)
            elif ann['category_id'] == person_cat:
                ann['category_id'] = 1
                ann['iscrowd'] = 0
                ann['ignore'] = 0
                new_ann.append(ann)
        for idx, ann in enumerate(new_ann):
            ann['id'] = idx + 1
        combined['categories'] = [{'id': 1, 'name': 'person', 'supercategory': ''}]
        combined['annotations'] = new_ann
        for image in combined['images']:
            image['file_name'] = image['file_name'].replace('.jpeg', '.jpg')

        # Get user input for output file name and directory
        output_file_name = st.text_input("Enter the output file name", "combined.json")
        output_dir = st.text_input("Enter the output directory path", ".")

        # Save the combined JSON file to disk
        output_file_path = os.path.join(output_dir, output_file_name)
        with open(output_file_path, "w") as f:
            json.dump(combined, f)

        # Display a download link for the combined JSON file
        st.download_button(
            label="Download the combined JSON file",
            data=open(output_file_path, "rb").read(),
            file_name=output_file_name,
            mime="application/json",
        )

        # Remove the temporary directory
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(temp_dir)

# Run the app
if __name__ == "__main__":
    app()