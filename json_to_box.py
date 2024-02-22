import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image, ImageFont, ImageDraw
import json
import os
from datetime import datetime
from pypresence import Presence
import time
import threading
import webbrowser
import shutil

data = None
json_file_name = None  # Stocker le nom du fichier JSON
nombre_convertit = 0
use_offset = False
skin_id = None
skin_image_path = None



#-------------------------------------------------------------------------------------------------




def discord_rich_presence():
    global nombre_convertit  
    client_id = '1208572315282047006'
    RPC = Presence(client_id)
    RPC.connect()

    try:
        while True:
            # Mettre à jour le statut toutes les 15 secondes (la limite est de 15 secondes par Discord)
            if nombre_convertit <= 1:
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




# Chemin du dossier "box"
box_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "box")

# Vérifier et créer le dossier "box" s'il n'existe pas
if not os.path.exists(box_folder):
    os.makedirs(box_folder)




#-------------------------------------------------------------------------------------------------




def charger_fichier():
    global data, json_file_name
    file_path = filedialog.askopenfilename(title="Select a JSON file", filetypes=[("JSON File", "*.json")])
    if file_path:
        json_file_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, 'r') as file:
            data = json.load(file)
        convert_button["state"] = tk.NORMAL  # Activer le bouton "Convert" une fois le fichier chargé
        info_label.config(text=f"File : {json_file_name}.json loads with succeed.")
        return data

#def charger_image():
    #global skin_image_path
    #skin_image_path = filedialog.askopenfilename(title="Select a skin image", filetypes=[("Image files", "*.png")])




#-------------------------------------------------------------------------------------------------




def convertir():
    global data, json_file_name, nombre_convertit, skin_id  # Déclarer data et json_file_name comme globales
    skin_id = skin_id_entry.get()  # Récupérer l'ID du skin à partir de la zone de texte
    try:
        if data and skin_id:  # Vérifier si l'ID du skin est saisi
            converted_data = convertir_json(data, use_offset)
            output_folder_name = generate_output_folder_name(json_file_name, skin_id)
            output_folder_path = os.path.join(box_folder, output_folder_name)
            output_file_name = generate_output_file_name(json_file_name, skin_id)
            output_file_path = os.path.join(output_folder_path, output_file_name)

            # Créer le dossier de sortie
            os.makedirs(output_folder_path, exist_ok=True)
            
            with open(output_file_path, 'w') as result_file:
                result_file.write(converted_data)
            
            # Ouvrir automatiquement le fichier après la conversion
            os.startfile(output_file_path)

            # Désactiver le bouton "Convert" après la conversion
            convert_button["state"] = tk.DISABLED

            # Créer le message avec un lien hypertexte
            message = f"Conversion complete. Check the file: Here."
            info_label.config(text=message, fg="blue", cursor="hand2")
            info_label.bind("<Button-1>", lambda e: webbrowser.open(output_folder_path))
        else:
            info_label.config(text=f"Please enter a skin ID.")
    except Exception as e:
        print(f"Error during conversion : {e}")
        info_label.config(text=f"Error during conversion")




#-------------------------------------------------------------------------------------------------

def set_skin_id(event):
    global skin_id
    skin_id = skin_id_entry.get()

def convertir_json(data, use_offset=False):
    result = ""
    offsets = {"HEAD": 0, "BODY": 0, "ARM0": 0, "ARM1": 0, "LEG0": 0, "LEG1": 0}
    base_coordinates = {"HEAD": -8, "BODY": 0, "ARM0": -2, "ARM1": -2, "LEG0": 0, "LEG1": 0}

    defined_names = ["0rightLeg", "1leftLeg", "0rightArm", "1leftArm", "head", "body"]

    result += "DISPLAYNAME:Skin Name\n"
    result += f"DISPLAYNAMEID:IDS_dlcskin_{skin_id}_DISPLAYNAME\n"
    result += "ANIM:0x7ff5fc10\n"
    result += "THEMENAME:Theme Name\n"
    result += "GAME_FLAGS:0x18\n"
    result += "FREE:1\n"

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

                # Utilisation des coordonnées de base uniquement si l'option d'offset est activée
                if use_offset:
                    result += f"BOX:{part_name} {origin[0]} {base_coordinates.get(part_name, 0)} {origin[2]} {size[0]} {size[1]} {size[2]} {uv[0]} {uv[1]}\n"
                else:
                    result += f"BOX:{part_name} {origin[0]} {origin[1]} {origin[2]} {size[0]} {size[1]} {size[2]} {uv[0]} {uv[1]}\n"

    if use_offset:
        for part_name, offset in offsets.items():
            if offset < 0:
                offset = abs(offset)
            else:
                offset = -offset
            result += f"OFFSET:{part_name} Y {offset}\n"

    return result


def toggle_offset():
    global use_offset
    use_offset = not use_offset
    offset_checkbutton.config(text="Offset ON" if use_offset else "Offset OFF")



#-------------------------------------------------------------------------------------------------



#def convert_image(image_path, output_path):
    # Ouvrir l'image d'origine
    #original_image = Image.open(image_path)
        
     # Créer une nouvelle image avec les mêmes dimensions
    #new_image = Image.new(original_image.mode, original_image.size)
        
     # Faire une copie de l'image d'origine
    #image_copy = original_image.copy()

    # Coller l'image d'origine sur la nouvelle image
    #new_image.paste(image_copy, (0, 0))

    # Enregistrer l'image convertie
    #new_image.save(output_path)




#-------------------------------------------------------------------------------------------------




def generate_output_folder_name(json_file_name, skin_id):
    # Générer le nom du dossier avec le format NOMDUJSON_YYMMDDHHMMSS_IDDUSKIN
    current_time = datetime.now()
    return f"{json_file_name}_{current_time.strftime('%y-%m-%d-%H-%M-%S')}_{skin_id}"

def generate_output_file_name(json_file_name, skin_id):
    # Générer le nom du fichier avec le format dlcskinIDDUSKIN.png.txt
    return f"dlcskin{skin_id}.png.txt"



#-------------------------------------------------------------------------------------------------
    


root = tk.Tk()
root.title("JSON To Box Converter")
root.geometry("500x250")
root.resizable(False, False)
IconPath = os.path.abspath("assets/icon.ico")
root.iconbitmap(IconPath)




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



root.configure(bg="#F0F0F0") 
root.option_add("*Font", "Helvetica 8") 
root.option_add("*Button.relief", "raised")  
root.option_add("*Button.bd", 2)  
root.option_add("*Button.bg", "#E0E0E0")  
root.option_add("*Button.activebackground", "#C0C0C0")
root.option_add("*Label.anchor", "w") 
root.option_add("*Label.bg", "#F0F0F0")
root.option_add("*Label.font", "Helvetica 8 bold") 
root.option_add("*Entry.relief", "sunken") 
root.option_add("*Entry.bd", 4) 
root.option_add("*Entry.bg", 2) 
root.option_add("*Checkbutton.bg", "#F0F0F0") 
root.option_add("*Checkbutton.font", "Helvetica 8") 
root.option_add("*Button.width", 20)  

# Bouton pour charger le fichier JSON
load_button = tk.Button(root, text="Load a JSON file", command=charger_fichier)
load_button.grid(row=0, column=0, padx=5, pady=45, sticky="w")
load_button.configure(relief="solid", bd=2)

# Bouton pour charger une image de skin
#load_image_button = tk.Button(root, text="Load a skin image", command=charger_image)
#load_image_button.grid(row=0, column=1, padx=5, pady=10, sticky="w")
#load_image_button.configure(relief="solid", bd=2)

# Entrée de texte pour saisir l'ID du skin
skin_id_label = tk.Label(root, text="Skin ID:")
skin_id_entry = tk.Entry(root)
skin_id_label.grid(row=2, column=0, padx=10, sticky="w")
skin_id_entry.grid(row=2, column=0, padx=60, sticky="ew")
skin_id_entry.bind("<Return>", set_skin_id)

# Bouton pour activer/désactiver l'option d'offset
use_offset_var = tk.BooleanVar()
offset_checkbutton = tk.Checkbutton(root, text="Offset", variable=use_offset_var, command=toggle_offset)
offset_checkbutton.grid(row=2, column=1, columnspan=2, padx=10, sticky="ew")
offset_checkbutton.config(width=10)

# Bouton pour convertir le JSON et créer un fichier texte
convert_button = tk.Button(root, text="Convert", command=convertir, state=tk.DISABLED)
convert_button.grid(row=7, column=3, padx=10, sticky="se")

skin_id_var = tk.StringVar ()

# Étiquette pour afficher les messages d'information
info_label = tk.Label(root, text="", anchor="center")
info_label.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")


root.mainloop()
