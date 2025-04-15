Volume Transfer

This Python script is designed to transfer an unattached and available Cloud Block Storage Volume from one Rackspace Cloud Account to another. You would need the credentials for both accounts in order to use this script.

Prerequisites:

- Python 3.x
- 2 Rackspace Cloud Accounts
- Both accounts' usernames and API keys
- Unattached & Available Cloud Block Storage Volume

Usage:

1. Clone the repository or download the script file.
2. Open a terminal or command prompt.
3. Navigate to the directory where the script is located.
4. Make the script executable (chmod +x volume_transfer.py)
4. Run the script using the following command:

python3 volume_transfer.py

5. Follow the on-screen prompts:
   - Enter the UUID of the Block Storage Volume you want to transfer.
   - Enter the username of the source account where the volume lives now.
   - Enter the API Key of the source account where the volume lives now.
   - Enter the region where the volume exists.
   - Enter the username of the destination account where the volume will be moved to.
   - Enter the API Key of the destination account where the volume will be moved to.
   - Enter the region where the volume exists.

6. Once the process completes, you will see the following messages indicating that the file splitting is completed.

    Creating volume transfer...
    Transfer created. Transfer ID: abcd-123-7123-asdasd, Auth Key: zxy1234566y

    Accepting volume transfer...

    Volume transfer completed successfully.

Author: Brian Abshier
License: This project is licensed under the MIT License.
