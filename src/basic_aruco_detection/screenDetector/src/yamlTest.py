import yaml
with open("aruco_codes.yaml") as file:
    yaml_file = yaml.safe_load(file)
print(yaml_file)
