import json

import httpx

http_verbs = ["get", "post", "put", "delete", "head", "options"]


def call_api(method_name, url, headers, body):
    # assume body is a string from the db here
    # this method called from run_cron_job.py for job execution
    print(f"body: {body} , type: {type(body)}")
    try:
        body_json = None
        if body is not None:
            body_json = json.loads(body)
        print(f"body json: {body_json}")

        if method_name.lower() in http_verbs:
            method_to_call = getattr(httpx, method_name.lower())
            print(f"method_to_call: {method_to_call}")

            response = None
            if method_name.lower() in ["get", "delete"] and body_json is not None:
                response = method_to_call(url, headers=headers, params=body_json)
            elif method_name.lower() in ["post", "put"]:
                response = method_to_call(url, headers=headers, json=body_json)

            assert response, "response is None"

            print("response from httpx call: ")
            print(response.status_code)
            print(response.text)
            return response
        else:
            print(f"Invalid method name: {method_name}")

    except json.JSONDecodeError as e:
        print(f"body json decode error: {e}")
        raise e


def get_example_test(headers):
    """
    simple GET example, get lnurlp
    """
    method_name = "GET"
    url = "http://localhost:5000/lnurlp/api/v1/links"
    body = json.dumps({"out": "true"})  # if there is no body pass None.
    response = call_api(method_name, url, headers, body)
    return response


def post_example_test():
    """
    simple POST example, create lnurlp
    """
    method_name = "POST"
    url = "http://localhost:5000/lnurlp/api/v1/links"
    headers = {"X-Api-Key": "70a745c683034ca2b22287d8d1538dee"}
    body_dict = {
        "description": "testlnurlp",
        "amount": 1000,
        "max": 1000,
        "min": 1000,
        "comment_chars": 0,
    }  # , "username": "foobar3"}
    body = json.dumps(body_dict)
    response = call_api(method_name, url, headers, body)
    return response


if __name__ == "__main__":

    data_list = [
        {"key": "X-Api-Key", "value": "70a745c683034ca2b22287d8d1538dee"},
        {"key": "Content-type", "value": "application/json"},
    ]
    json_data = json.dumps(data_list, indent=4)
    data = {}
    for e in data_list:
        print(f'key: {e["key"]}, value: {e["value"]}')
        data.update({e["key"]: e["value"]})

    print(json.dumps(data))

    get_example_test(headers=data)

    post_example_test()

    print("Continue here with method_name calling response ")
