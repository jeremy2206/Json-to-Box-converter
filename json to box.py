import tkinter as tk
from tkinter import filedialog
import json
import os
from datetime import datetime

data = None
json_file_name = None  # Stocker le nom du fichier JSON

# Chemin du dossier "box"
box_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "box")

# Vérifier et créer le dossier "box" s'il n'existe pas
if not os.path.exists(box_folder):
    os.makedirs(box_folder)

def charger_fichier():
    global data, json_file_name  # Déclarer data et json_file_name comme globales
    file_path = filedialog.askopenfilename(title="Sélectionner un fichier JSON", filetypes=[("Fichiers JSON", "*.json")])
    if file_path:
        json_file_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, 'r') as file:
            data = json.load(file)
        convert_button["state"] = tk.NORMAL  # Activer le bouton "Convert" une fois le fichier chargé
        info_label.config(text=f"Fichier {json_file_name}.json chargé avec succès.")
        return data

def convertir():
    global data, json_file_name  # Déclarer data et json_file_name comme globales
    try:
        if data:
            converted_data = convertir_json(data)
            output_file_name = generate_output_file_name(json_file_name)
            output_file_path = os.path.join(box_folder, output_file_name)
            
            with open(output_file_path, 'w') as result_file:
                result_file.write(converted_data)
            info_label.config(text=f"Conversion terminée. Vérifiez le fichier {output_file_name}.")
            print(f"Conversion terminée. Vérifiez le fichier {output_file_name}.")
            
            # Ouvrir automatiquement le fichier après la conversion
            os.startfile(output_file_path)
            
            # Désactiver le bouton "Convert" après la conversion
            convert_button["state"] = tk.DISABLED
    except Exception as e:
        print(f"Erreur lors de la conversion : {e}")
        info_label.config(text=f"Erreur lors de la conversion. Vérifiez la console pour plus d'informations.")

def convertir_json(data):
    result = ""
    
    for bone in data.get("geometry.cosmetic", {}).get("bones", []):
        name = bone.get("name", "")
        
        cubes = bone.get("cubes", [])
        for cube in cubes:
            size = cube.get("size", [0, 0, 0])
            uv = cube.get("uv", [0, 0])
            origin = cube.get("origin", [0, 0, 0])
            
            part_name = None
            if name == "0rightLeg":
                part_name = "LEG0"
                origin[0] += 2  # +2x
            elif name == "1leftLeg":
                part_name = "LEG1"
                origin[0] -= 2  # -2x
            elif name == "0rightArm":
                part_name = "ARM0"
                origin[0] += 5 # +5x
                origin[1] -= 14  # -14y
            elif name == "1leftArm":
                part_name = "ARM1"
                origin[0] -= 5  # -5x
                origin[1] -= 14  # -14y
            elif name == "head":
                part_name = "HEAD"
                origin[1] -= 32  # -32y 
            elif name == "body":
                part_name = "BODY"
                origin[1] -= 12  # -12y
            else:
                part_name = "UNKNOWN"
            
            # Conversion de la ligne
            result += f"BOX:{part_name} {origin[0]} {origin[1]} {origin[2]} {size[0]} {size[1]} {size[2]} {uv[1]} {uv[0]}\n"
    
    return result

def generate_output_file_name(json_file_name):
    # Générer le nom du fichier avec le format NOMDUJSON_YYMMDDHHMMSS
    current_time = datetime.now()
    return f"{json_file_name}_{current_time.strftime('%y%m%d%H%M%S')}.txt"

root = tk.Tk()
root.title("Convertisseur JSON")

# Bouton pour charger le fichier JSON
load_button = tk.Button(root, text="Charger un fichier JSON", command=charger_fichier)
load_button.pack(pady=10)

# Bouton pour convertir le JSON et créer un fichier texte
convert_button = tk.Button(root, text="Convert", command=convertir, state=tk.DISABLED)
convert_button.pack(pady=10)

# Étiquette pour afficher les messages d'information
info_label = tk.Label(root, text="")
info_label.pack(pady=10)


root.mainloop()
