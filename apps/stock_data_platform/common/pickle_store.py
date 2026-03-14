import os
import pickle


def save(obj, file_path):
    dir_name = os.path.dirname(file_path)
    if dir_name and not os.path.exists(dir_name):
        print(f"[{dir_name}] Not Exists.\n\t Create New Folder ...")
        os.makedirs(dir_name)
    with open(file_path, "wb") as file_obj:
        pickle.dump(obj, file_obj)
    print("Save successfully.")


def load(file_path):
    with open(file_path, "rb") as file_obj:
        return pickle.load(file_obj)
