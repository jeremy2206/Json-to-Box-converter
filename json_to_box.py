import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image, ImageFont, ImageDraw
import json
import os
from datetime import datetime
from pypresence import Presence
import time
import threading

box_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "box")
data = None
json_file_name = None 
nombre_convertit = 0
use_offset = False

# Vérifier et créer le dossier "box" s'il n'existe pas
if not os.path.exists(box_folder):
    os.makedirs(box_folder)

def charger_fichier():
    global data, json_file_name  # Déclarer data et json_file_name comme globales
    file_path = filedialog.askopenfilename(title="Select a JSON file", filetypes=[("JSON File", "*.json")])
    if file_path:
        json_file_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, 'r') as file:
            data = json.load(file)
        convert_button["state"] = tk.NORMAL  # Activer le bouton "Convert" une fois le fichier chargé
        info_label.config(text=f"File : {json_file_name}.json loads with succeed.")
        return data

def convertir():
    global data, json_file_name, nombre_convertit  # Déclarer data et json_file_name comme globales
    try:
        if data:
            converted_data = convertir_json(data, use_offset)
            output_file_name = generate_output_file_name(json_file_name)
            output_file_path = os.path.join(box_folder, output_file_name)

            with open(output_file_path, 'w') as result_file:
                result_file.write(converted_data)
            info_label.config(text=f"Conversion complete. Check the file : {output_file_name}.")
            print(f"Conversion complete. Check the file : {output_file_name}.")
            nombre_convertit += 1

            # Ouvrir automatiquement le fichier après la conversion
            os.startfile(output_file_path)

            # Désactiver le bouton "Convert" après la conversion
            convert_button["state"] = tk.DISABLED
    except Exception as e:
        print(f"Error during conversion : {e}")
        info_label.config(text=f"Error during conversion")

def convertir_json(data, use_offset=False):
    result = ""
    offsets = {"HEAD": 0, "BODY": 0, "ARM0": 0, "ARM1": 0, "LEG0": 0, "LEG1": 0}
    base_coordinates = {"HEAD": -8, "BODY": 0, "ARM0": -2, "ARM1": -2, "LEG0": 0, "LEG1": 0}

    defined_names = ["0rightLeg", "1leftLeg", "0rightArm", "1leftArm", "head", "body"]

    for bone in data.get("geometry.cosmetic", {}).get("bones", []):
        name = bone.get("name", "")
        parent = bone.get("parent", "")

        if name in defined_names or parent in defined_names:
            cubes = bone.get("cubes", [])
            for cube in cubes:
                size = [round(val) for val in cube.get("size", [0, 0, 0])]
                uv = [round(val) for val in cube.get("uv", [0, 0])]
                origin = [round(val) for val in cube.get("origin", [0, 0, 0])]

                part_name = None
                if name == "0rightLeg" or parent == "0rightLeg":
                    part_name = "LEG0"
                    origin[0] += 2  # +2x
                    origin[1] += 12  # 0x -> +12y
                elif name == "1leftLeg" or parent == "1leftLeg":
                    part_name = "LEG1"
                    origin[0] -= 2  # -2x
                    origin[1] += 12  # 0x -> +12y
                elif name == "0rightArm" or parent == "0rightArm":
                    part_name = "ARM0"
                    origin[0] += 5  # +5x
                    origin[1] += 22  # -14y -> 22y
                elif name == "1leftArm" or parent == "1leftArm":
                    part_name = "ARM1"
                    origin[0] -= 5  # -5x
                    origin[1] += 22  # -14y -> +22y
                elif name == "head" or parent == "head":
                    part_name = "HEAD"
                    origin[1] += 24  # -32y -> +24y
                elif name == "body" or parent == "body":
                    part_name = "BODY"
                    origin[1] += 24  # -12y -> +24y
                else:
                    part_name = "UNKNOWN"

                if use_offset:
                    offset = base_coordinates.get(part_name, 0) - origin[1]
                    offsets[part_name] = offset

                # Conversion de la ligne
                result += f"BOX:{part_name} {origin[0]} {base_coordinates.get(part_name, 0)} {origin[2]} {size[0]} {size[1]} {size[2]} {uv[0]} {uv[1]}\n"

    if use_offset:
        for part_name, offset in offsets.items():
            if offset < 0:
                offset = abs(offset)
            else:
                offset = -offset
            result += f"OFFSET:{part_name} Y {offset}\n"
    else:
        for part_name, offset in offsets.items():
            result += f"OFFSET:{part_name} Y {offset}\n"

    return result

def generate_output_file_name(json_file_name):
    # Générer le nom du fichier avec le format NOMDUJSON_YYMMDDHHMMSS
    current_time = datetime.now()
    return f"{json_file_name} {current_time.strftime('%y-%m-%d-%H-%M-%S')}.txt"

def toggle_offset():
    global use_offset
    use_offset = not use_offset
    offset_checkbutton.config(text="Offset ON" if use_offset else "Offset OFF")

#----------------------------------------------------------------------------------------

def discord_rich_presence():
    global nombre_convertit  # Déclarer nombre_convertit comme une variable globale
    # Initialiser Discord Rich Presence avec l'ID de votre application
    client_id = '1208572315282047006'
    RPC = Presence(client_id)
    RPC.connect()

    # Boucle pour maintenir la connexion
    try:
        while True:
            # Mettre à jour le statut toutes les 15 secondes (la limite est de 15 secondes par Discord)
            if nombre_convertit<=1:
                RPC.update(state="Converting a skin", details=f"{nombre_convertit} skin converted", large_image="logo", large_text=":)")
            else:
                RPC.update(state="Converting a skin", details=f"{nombre_convertit} skins converted", large_image="logo", large_text=":)")
            time.sleep(15)  
    except KeyboardInterrupt:
        RPC.close()

# Exécuter Discord Rich Presence dans un thread séparé
discord_thread = threading.Thread(target=discord_rich_presence)
discord_thread.daemon = True
discord_thread.start()

#-------------------------------------------------------------------------------------------------

root = tk.Tk()
root.title("JSON To Box Converter")
root.geometry("500x250")
root.resizable(False, False)
IconPath = os.path.abspath("assets/icon.ico")
root.iconbitmap(IconPath)

#-------------------------------------------------------------------------------------------------

# Global Background
Background = tk.Label(root, bg="#383838")
Background.place(x=0, y=0, width=1000, height=1000)

#-------------------------------------------------------------------------------------------------
#   **--Title and Background--**

FontMojangles = os.path.abspath("assets/Mojangles.ttf")
TitleAppText = "JSON To Box Converter"
TitleAppFontSize = 25
TitleAppFont = ImageFont.truetype(FontMojangles, TitleAppFontSize)

# Image and Border
TitleAppImageWidth = 500
TitleAppImageHeight = 35
TitleAppImage = Image.new("RGBA", (TitleAppImageWidth, TitleAppImageHeight), (255, 255, 255, 0))
TitleAppDraw = ImageDraw.Draw(TitleAppImage)
TitleAppOutlineColor = (0, 0, 0)
TitleAppOutlinePosition = (89.5, 4)
TitleAppDraw.text(TitleAppOutlinePosition, TitleAppText, font=TitleAppFont, fill=TitleAppOutlineColor)

# Draw Text
TitleAppTextColor = (255, 255, 255)
TitleAppTextPosition = (87, 2)
TitleAppDraw.text(TitleAppTextPosition, TitleAppText, font=TitleAppFont, fill=TitleAppTextColor)

# Convert Image to tk
TitleAppImagetk = ImageTk.PhotoImage(TitleAppImage)

# Show Image
TitleApp = tk.Label(root, image=TitleAppImagetk, bg="#585858")
TitleApp.place(x=0, y=0)

#-------------------------------------------------------------------------------------------------

root.columnconfigure(0, minsize=50)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
root.grid_columnconfigure((0, 1, 2), minsize=0, weight=1)

# Bouton pour charger le fichier JSON
load_button = tk.Button(root, text="Load a JSON file", command=charger_fichier)
load_button.grid(row=1, column=1, pady=10)
load_button.configure(relief="solid", bd=2)

# Bouton pour activer/désactiver l'option d'offset
use_offset_var = tk.BooleanVar()
offset_checkbutton = tk.Checkbutton(root, text="Offset", variable=use_offset_var, command=toggle_offset)
offset_checkbutton.grid(row=2, column=1, pady=10)

# Bouton pour convertir le JSON et créer un fichier texte
convert_button = tk.Button(root, text="Convert", command=convertir, state=tk.DISABLED)
convert_button.grid(row=3, column=1, pady=10)
convert_button.configure(relief="solid", bd=2)

# Étiquette pour afficher les messages d'information
info_label = tk.Label(root, text="")
info_label.grid(row=4, column=1, pady=20)

root.mainloop()