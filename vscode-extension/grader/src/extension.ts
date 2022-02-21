import * as vscode from 'vscode';
import * as net from 'net';

enum Message {
	start = 1,
	review = 2,
	stop = 3
}

function sendMessage(message: Message, socket: net.Socket) {
	let buf = Buffer.alloc(1, message);
	socket.write(buf);
}

var client: net.Socket;

export function activate(context: vscode.ExtensionContext) {
	let workdir = process.env.GRADER_WORKDIR;

	if (workdir === undefined) {
		vscode.window.showErrorMessage("GRADER_WORKDIR environment variable is not defined!");
		return;
	}

	let sockPath = workdir + "/sock";
	client = net.createConnection(sockPath)
		.on('connect', () => {
			vscode.window.showInformationMessage("Connected to grader script");
		})
		.on('data', (data) => {
			let s = data.toString();
			if (s.startsWith("__")) {
				if (s === "__stop") {
					vscode.window.showInformationMessage("Stop command received");
					vscode.commands.executeCommand('workbench.action.closeWindow');
				} else {
					vscode.window.showErrorMessage("Invalid command received: " + s);
				}
			} else {
				vscode.window.showInformationMessage("Student id: " + s);
			}
		});

	let started = false;
	let disposable = vscode.commands.registerCommand('grader.startGrading', () => {
		if (!started) {
			vscode.window.showInformationMessage("Sending start command");
			sendMessage(Message.start, client);
			started = true;
		} else {
			vscode.workspace.saveAll().then((good) => {
				if (good) {
					vscode.window.showInformationMessage("Posting review");
					sendMessage(Message.review, client);
				} else {
					vscode.window.showErrorMessage("Unable to save all files");
				}
			});
		}
	});

	context.subscriptions.push(disposable);
}

// this method is called when your extension is deactivated
export function deactivate() {
	sendMessage(Message.stop, client);
}
