import yaml
import argparse

def parse_yaml_file(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)

    for service_name, service_details in data['services'].items():
        print(f"{service_name}:")
        for key, value in service_details.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict):
                        print(f"    {sub_key}:")
                        for sub_sub_key, sub_sub_value in sub_value.items():
                            print(f"      {sub_sub_key}: {sub_sub_value}")
                    else:
                        print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        print()

def main():
    parser = argparse.ArgumentParser(description='Parse a build.yaml file.')
    parser.add_argument('file_path', type=str, help='The path to the build.yaml file.')
    args = parser.parse_args()

    parse_yaml_file(args.file_path)

if __name__ == "__main__":
    main()