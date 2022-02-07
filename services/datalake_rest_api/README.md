# About

REST API for Azure Blob Storage / DataLake access for DataFabrikken v2 demo.

Much of the code here has been borrowed/copied from:  https://github.com/tonybaloney/ants-azure-demos/tree/master/fastapi-functions

# To Deploy To Azure Functions from VSCode

These steps assume that you are using the [Azure Functions VS Code Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions).

Step 1:  Install the [Azure Functions VS Code Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions).

Step 2:  Open your project in VSCode.  VSCode will automatically create a virtual environment for you and install all dependencies.

Step 3:  Run your Azure Function locally:

  * Press F5.

Verify that your app is running by going to:  http://localhost:7071.  You should see a JSON response.

Step 4:  Deploy your function to Azure:

  * Open the VSCode Command Palette.
  * Run "Azure Functions:  Deploy to Function App."
  * Follow the prompts and wait a few minutes for everything to deploy.

Verify that your app is running by going to:  https://<APP_NAME>.azurewebsites.net.  You should see the same message as in Step 4.