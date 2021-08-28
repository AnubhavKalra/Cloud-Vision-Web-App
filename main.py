from flask import Flask, render_template, request
import os
from google.resumable_media import requests
import io
from io import BytesIO
import os.path
from google.cloud import vision_v1
from google.cloud import storage
import pandas as pd
import glob
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './input/'

@app.route("/")
def home():
    return render_template("home.html")
    
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/uploader" , methods=['GET', 'POST'])
def uploader():
    if request.method=='POST':
        f = request.files['apikey']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], (f.filename)))
        g = request.files['image']
        g.save(os.path.join(app.config['UPLOAD_FOLDER'], (g.filename)))
        return final(f,g)

@app.route("/final")
def final(f,g):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'./input/'+f.filename
    client = vision_v1.ImageAnnotatorClient()
    image_path = './input/'+g.filename
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision_v1.types.Image(content=content)
    response1 = client.label_detection(image=image)
    response2 = client.web_detection(image=image)
    response3 = client.object_localization(image=image)
    response4 = client.text_detection(image=image)

    labels = response1.label_annotations
    annotations = response2.web_detection
    objects = response3.localized_object_annotations
    texts = response4.text_annotations

    df1 = pd.DataFrame(columns=['description'])
    for label in labels:
        df1 = df1.append(
            dict(
                description=label.description
            ), ignore_index=True
        )
    df2 = pd.DataFrame(columns=['best_guess_labels', 'web_entities'])
    if annotations.best_guess_labels:
        for annotation in annotations.best_guess_labels:
            df2 = df2.append(
                dict(
                best_guess_labels = annotation.label
                ), ignore_index=True
            )
    if annotations.web_entities:
        for entity in annotations.web_entities:
            df2 = df2.append(
                dict(
                web_entities = entity.description
                ), ignore_index=True
            )
    df3 = pd.DataFrame(columns=['localized_objects'])
    for object_ in objects:
        df3 = df3.append(
                dict(
                localized_objects = object_.name
                ), ignore_index=True
            )
    df4 = pd.DataFrame(columns=['text_detection'])
    j=0
    for text in texts:
        if j==0:
            j=j+1
            continue
        df4 = df4.append(
                dict(
                text_detection = text.description
                ), ignore_index=True
            )
    output_file_1="output/result1.txt"
    output_file_2="output/result2.txt"
    output_file_3="output/result3.txt"
    output_file_4="output/result4.txt"
    df1 = df1.replace(np.nan, '', regex=True)
    df2 = df2.replace(np.nan, '', regex=True)
    df3 = df3.replace(np.nan, '', regex=True)
    df4 = df4.replace(np.nan, '', regex=True)
    print(df1)
    with open(output_file_1, 'w', encoding="utf-8") as l1:
        dfAsString = df1.to_string(header=False, index=False)
        l1.write(dfAsString)
    print(df2)
    with open(output_file_2, 'w', encoding="utf-8") as l2:
        dfAsString = df2.to_string(header=False, index=False)
        l2.write(dfAsString)
    print(df3)
    with open(output_file_3, 'w', encoding="utf-8") as l3:
        dfAsString = df3.to_string(header=False, index=False)
        l3.write(dfAsString)
    print(df4)
    with open(output_file_4, 'w', encoding="utf-8") as l4:
        dfAsString = df4.to_string(header=False, index=False)
        l4.write(dfAsString)

    return("Hopefully it's successfull")


if __name__ == "__main__":
    app.run(debug=True)
