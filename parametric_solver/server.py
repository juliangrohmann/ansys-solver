from flask import Flask, jsonify


class SolverServer:
    """
    A flask web-server that provides the endpoint from which its client
    counterparts (SolverClient) retrieve parametric samples to solve.

    For use with the SLURM compute cluster.

    Endpoints
    ---------
    GET /sample
        Responses:

        200: Sample is available and returned in json format.

        404: All samples have been solved.
    """
    def __init__(self):
        self.app = Flask(__name__)
        self.samples = []

        @self.app.route('/sample', methods=['GET'])
        def get_sample():
            if self.samples:
                sample = self.samples.pop(0)
                print(f"Serving sample", ', '.join(['{:.2e}'.format(num) for num in sample]), "...")
                return jsonify(sample), 200
            return jsonify({"message": "No samples available"}), 404

    def add_sample(self, sample):
        """
        Adds a sample to serve to the clients.

        Parameters
        ----------
        sample: Any
            The sample to add. See documentation of the client's parametric solver for type/format.
        """
        self.samples.append(sample)

    def run(self, host='127.0.0.1', port=5000, debug=True):
        """
        Starts the server.

        Parameters
        ----------
        host: str,
            The hostname (i.e. IP address) on which the server will run.

        port: int
            The port on which the srever will run.

        debug: bool, optional
            If True, prints verbose debug output,
            otherwise only prints minimal output.
        """
        self.app.run(host=host, port=port, debug=debug)
