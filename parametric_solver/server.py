from flask import Flask, jsonify


class SolverServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.samples = []

        @self.app.route('/sample', methods=['GET'])
        def get_sample():
            if self.samples:
                sample = self.samples.pop(0)
                print(f"Serving sample {sample} ...")
                return jsonify(sample), 200
            return jsonify({"message": "No samples available"}), 404

    def add_sample(self, sample):
        self.samples.append(sample)

    def run(self, host='127.0.0.1', port=5000, debug=True):
        self.app.run(host=host, port=port, debug=debug)
