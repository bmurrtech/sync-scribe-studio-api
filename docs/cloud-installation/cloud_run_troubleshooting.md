# Cloud Run Troubleshooting Guide

This guide provides a structured approach to diagnosing and resolving common issues encountered when deploying to Google Cloud Run, with a focus on import errors related to shared object files.

## 1. Symptoms

The primary symptom of the issues covered in this guide is a failing or crashing service on Cloud Run, accompanied by one of the following error messages in the logs:

*   `ImportError: libGL.so.1: cannot open shared object file: No such file or directory`
*   `ImportError: libsqlite3.so.0: cannot open shared object file: No such file or directory`
*   `ImportError: libssl.so.1.1: cannot open shared object file: No such file or directory`
*   `ImportError: libnss3.so: cannot open shared object file: No such file or directory`
*   Other `ImportError` messages indicating a missing shared object (`.so`) file.
*   The service fails to start, and the logs show that the container has crashed or is in a crash loop.

## 2. Probable Causes

Based on internal project documentation and external resources, the following are the most likely causes of these errors:

1.  **Missing System Dependencies:** The Docker image being deployed to Cloud Run is missing essential system-level libraries (shared object files, or `.so` files) that the application or one of its dependencies requires to function correctly. This is the most common cause of the `ImportError` messages listed above.
2.  **Incorrect Docker Image Architecture:** Cloud Run services run on `linux/amd64` (also known as x86_64) infrastructure. If a Docker image is built on a machine with a different architecture, such as an Apple Silicon Mac (`arm64`), and is not built as a multi-arch image with an `amd64` variant, it will fail to run on Cloud Run.
3.  **Incorrect Environment Variables:** The application may fail to initialize correctly if the required environment variables are not set, are incorrect, or are improperly formatted in the Cloud Run service configuration. This can sometimes lead to secondary errors, including import errors if a library fails to load due to a missing configuration. The required environment variables are documented in the [GCP installation guide](./gcp.md).
4.  **Long-Running Processes:** As noted in the project's `README.md`, Cloud Run may terminate processes that run for longer than 5-10 minutes. While this may not directly cause an `ImportError`, it is a common issue that can cause a service to fail and should be considered if the error occurs after a long processing time.

## 3. Diagnostic Commands

To effectively diagnose the root cause of a Cloud Run issue, use the following commands and procedures:

1.  **Check Cloud Run Logs:** The first and most important step is to inspect the logs of the failing Cloud Run service. The logs will contain the specific error message, including the name of the missing shared object file.
    *   **Via Google Cloud Console:** Navigate to the Cloud Run service in the Google Cloud Console and view the "Logs" tab.
    *   **Via `gcloud` CLI:** Use the following command to tail the logs of your service. Replace `<service-name>` and `<project-id>` with your service's name and your Google Cloud project ID.
        ```bash
        gcloud run services logs tail <service-name> --project <project-id>
        ```

2.  **Inspect the Docker Image Architecture:** To verify that the Docker image has the correct architecture for Cloud Run (`linux/amd64`), use the `docker manifest inspect` command. This command will show the different architecture variants available for the image.
    ```bash
    docker manifest inspect stephengpope/sync-scribe-studio-api:latest
    ```
    Look for an entry in the manifest with `"architecture": "amd64"` and `"os": "linux"`.

3.  **Inspect the Docker Image Contents:** If you have access to the `Dockerfile` or can run the image locally, you can inspect its contents to see if the required shared libraries are present.
    *   **If you have the `Dockerfile`:** Review the `RUN` instructions to see which packages are being installed.
    *   **If you can run the image locally:** You can start a shell in the container and look for the missing file:
        ```bash
        docker run -it --entrypoint /bin/bash stephengpope/sync-scribe-studio-api:latest
        find / -name "libGL.so.1"
        ```

## 4. Resolutions/Work-arounds

Once you have diagnosed the issue, use one of the following resolutions:

1.  **Install Missing Dependencies in the `Dockerfile`:** The most common solution is to add commands to the `Dockerfile` to install the missing system dependencies using the appropriate package manager (e.g., `apt-get` for Debian-based images).
    *   **Example:** If `libGL.so.1` is missing, you would add the following to your `Dockerfile`:
        ```dockerfile
        RUN apt-get update && apt-get install -y libgl1-mesa-glx
        ```
    *   After modifying the `Dockerfile`, you will need to rebuild and push the image to the container registry.

2.  **Build a Multi-Arch Docker Image:** To avoid architecture-related issues, always build your Docker image with support for `linux/amd64`. As per the project rules, you can use `docker buildx` to build a multi-arch image.
    ```bash
    docker buildx create --use
    docker buildx build --platform linux/amd64 -t your-repo/image:latest . --push
    ```

3.  **Verify Environment Variables:** Carefully review the environment variables set in your Cloud Run service configuration and ensure they match the requirements in the [GCP installation guide](./gcp.md). Pay close attention to formatting, especially for the `GCP_SA_CREDENTIALS` variable, which should contain the entire JSON key file.

4.  **Use a Different Base Image:** If the current base image is missing a large number of dependencies, it may be more efficient to switch to a different base image that is better suited to your application's needs. For example, using a base image that comes with more of the required libraries pre-installed can simplify the `Dockerfile` and reduce build times.

