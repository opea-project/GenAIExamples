import requests
import json
import argparse
import os
import tqdm

def get_args():
    parser = argparse.ArgumentParser(description='Index data')
    parser.add_argument('--host_ip', type=str, default='localhost', help='Host IP')
    parser.add_argument('--port', type=int, default=6007, help='Port')
    parser.add_argument('--filedir', type=str, default=None, help='file directory')
    parser.add_argument('--filename', type=str, default=None, help='file name')
    parser.add_argument("--chunk_size", type=int, default=10000, help="Chunk size")
    parser.add_argument("--chunk_overlap", type=int, default=0, help="Chunk overlap")
    args = parser.parse_args()
    return args

def split_jsonl_into_txts(jsonl_file):
    docs = []
    n = 0
    with open(jsonl_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            docs.append(data["doc"])
            n+=1
            if n>2:
                break
    return docs

def write_docs_to_disk(docs, output_folder):
    output_files = []
    for i, text in enumerate(docs):
        output = os.path.join(output_folder, str(i) + '.txt')
        output_files.append(output)
        with open(output, 'w') as f:
            f.write(text)
    return output_files

def delete_files(files):
    for file in files:
        os.remove(file)

def main():
    args = get_args()
    print(args)

    host_ip = args.host_ip
    port = args.port
    proxies = {"http": ""}
    url = "http://{host_ip}:{port}/v1/dataprep".format(host_ip=host_ip, port=port)

    # Split jsonl file into json files
    files = split_jsonl_into_txts(os.path.join(args.filedir, args.filename))
    file_list = write_docs_to_disk(files, args.filedir)

    print(file_list)
    
    for file in tqdm.tqdm(file_list):
        print("Indexing file: ", file)
        files = [('files', (f, open(f, 'rb'))) for f in [file]]
        payload = {"chunk_size": args.chunk_size, "chunk_overlap": args.chunk_overlap}
        resp = requests.request('POST', url=url, headers={}, files=files, data=payload, proxies=proxies)
        print(resp.text)

    print("Removing temp files....")
    delete_files(file_list)
    print('ALL DONE!')

if __name__ == '__main__':
    main()