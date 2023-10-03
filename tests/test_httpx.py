import json
import httpx

http_verbs = ['get', 'post', 'put', 'delete', 'head', 'options']

def call_api(method_name, url, headers, body):
    # assume body is a string from the db here
    # this method called from run_cron_job.py for job execution
    print(f'body: {body} , type: {type(body)}')
    try:
        body_json = None
        if body is not None:
            body_json = json.loads(body)
        print(f'body json: {body_json}')

        if method_name.lower() in http_verbs:
            method_to_call = getattr(httpx, method_name.lower())
            print(f'method_to_call: {method_to_call}')
            
            if body_json is not None:
                response = method_to_call(url, headers=headers, json=body_json)
            else:
                response = method_to_call(url, headers=headers, params=body)
            print("response from httpx call: ")
            print(response.status_code)
            print(response.text)
            return response
        else:
            print(f'Invalid method name: {method_name}')

    except json.JSONDecodeError as e:
        print(f'body json decode error: {e}')
        raise e


def get_example_test():
    ''' 
    simple GET example, get lnurlp
    '''
    method_name = "GET"
    url = "http://localhost:5000/lnurlp/api/v1/links"
    headers = {"X-Api-Key": "70a745c683034ca2b22287d8d1538dee", 
                "content": "application/text"}
    body = None  # if there is no body pass None.
    response = call_api(method_name, url, headers, body)
    return response


def post_example_test():
    '''
    simple POST example, create lnurlp
    '''
    method_name = 'POST'
    url = "http://localhost:5000/lnurlp/api/v1/links"
    headers = {"X-Api-Key": "70a745c683034ca2b22287d8d1538dee"}
    body_dict = {"description": "testlnurlp", "amount": 1000, "max": 1000, "min": 1000, "comment_chars": 0, "username": "foobarbaz"}
    body = json.dumps(body_dict)
    response = call_api(method_name, url, headers, body)
    return response



if __name__ == "__main__":

    get_example_test()

#    post_example_test()

    print('Continue with method_name calling response ')   
    # procced with await save_job_execution(response=response, jobID=jobID, adminkey=adminkey)

