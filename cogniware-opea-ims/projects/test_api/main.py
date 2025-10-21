from flask import Flask, request, jsonify

app = Flask(__name__)

# Sample database (in-memory)
items = []

@app.route('/api/items', methods=['GET'])
def get_items():
    return jsonify({"items": items, "count": len(items)})

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    item = {"id": len(items) + 1, "data": data}
    items.append(item)
    return jsonify(item), 201

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = next((i for i in items if i['id'] == item_id), None)
    if item:
        return jsonify(item)
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
