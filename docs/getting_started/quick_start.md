# Quick Start
1. Clone the Git repo [Analitiq AI](https://github.com/analitiq-ai/analitiq)
2. Set up `profiles.yml`. In order to understand where and how to place it, please read [Profiles Configuration](/getting_started/profiles/)
3. Set up `project.yml` in root directory. In order to understand more about it, please check out [Project Configuration](/getting_started/project/)
4. Run the example file `example.py` located in the root directory, to ask your first question.

## Configuration files
There are 2 configuration files:

1. `profiles.yaml` - this file has all the secrets and connections needed to connect to LLMs, VectorDBs, Databases. Because you may have different production and development environments, profiles.yaml allows you to define multiple profiles (and multiple credentials).

2. `project.yaml` - this file has the parameters needed for your particular project, including what profile to use. You can define the profile in `profile` parameter.
   Once you have your project deployed, you can specify which profile to be used by that particular project in `project.yaml`.

