## Release

Executable Download: [Exodus (Windows)](https://github.com/Infinite-Unknown/APSpace-Bruteforce/raw/refs/heads/main/Exodus.exe) [ver 1.0] 

# Exodus

A Python tool designed to bruteforce OTPs (One-Time Passwords).

## Description

    Exodus is a multi-threaded application that attempts to guess OTPs by iterating through possible combinations. It includes a GUI for monitoring progress and supports pausing/resuming.

## Configuration & Usage

To use this tool, you need to provide a valid session in the form of a cURL command. Follow these steps to obtain it:

1.  **Trigger a Failed OTP Request:**
    *   Go to the target attendance page.
    *   Enter a wrong OTP (e.g., `000`) to intentionally fail the check until the "Failed" notification pops out.

2.  **Capture the Request:**
    *   Press `Ctrl + Shift + I` to open Developer Tools.
    *   Navigate to the **Network** tab in the DevTools window.
    *   Look for the network request corresponding to the failed OTP attempt (usually a `POST` request to `graphql`).

3.  **Copy as cURL:**
    *   Right-click on that network request.
    *   Hover over **Copy** and select **Copy as cURL (bash)**.

4.  **Save and Import:**
    *   Paste the copied cURL command into a text file (e.g., `config.txt`) and save it.
    *   Run the Exodus tool.
    *   Select **Option 4** from the main menu.
    *   Browse and select the text file you created. The tool will parse the cURL and extract the necessary headers and session details for the app to work.

## Disclaimer

This tool is for educational purposes only. Unauthorized use against systems you do not own or have check permission to test is illegal.
