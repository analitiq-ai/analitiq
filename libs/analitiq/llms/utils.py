def get_prompt_extra_info(prompts):
    """
    Get the user prompt and extra information based on the provided prompts.

    :param prompts: A dictionary containing prompts, including original, refined, feedback, and hints.
    :type prompts: dict
    :return: A tuple containing the user prompt and additional information.
    :rtype: tuple[str, str]
    """
    extra_info = ""

    if len(prompts["refined"]) > 10:
        user_prompt = prompts["refined"]
    else:
        user_prompt = prompts["original"]

    if len(prompts["feedback"]) > 10:
        extra_info = (
            extra_info
            + f"Your previous thoughts about this query were '{prompts['feedback']}'.\n"
        )

    if len(prompts["hints"]) > 10:
        extra_info = (
            extra_info
            + f"Your previous thoughts about this query were '{prompts['hints']}'.\n"
        )

    return user_prompt, extra_info
