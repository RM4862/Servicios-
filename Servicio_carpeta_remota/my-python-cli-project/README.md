# My Python CLI Project

This project implements a simple XML-RPC server and client that allows users to list the contents of a specified directory on the server.

## Project Structure

```
my-python-cli-project
├── src
│   ├── servidor_cr.py      # XML-RPC server implementation
│   ├── cliente_cr.py       # Client to interact with the server
│   └── cli.py              # Command-line interface for the client
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd my-python-cli-project
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Starting the Server

To start the XML-RPC server, run the following command in your terminal:
```
python src/servidor_cr.py
```
The server will listen on `localhost` at port `8000`.

### Using the Client

To list the contents of a remote directory, run the client script:
```
python src/cliente_cr.py
```
You will be prompted to enter the path of the remote directory. The client will display the contents or an error message if applicable.

### Command-Line Interface

The project includes a command-line interface for easier interaction. You can run the CLI with:
```
python src/cli.py
```
This will provide a user-friendly way to specify the directory path and view the results.

## Dependencies

- xmlrpc.client (for client-server communication)
- argparse or click (for command-line interface)

## License

This project is licensed under the MIT License. See the LICENSE file for more details.