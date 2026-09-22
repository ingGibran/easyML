from redis import Redis
import json

client = Redis(
    host='host',
    port=6379,
    decode_responses=True
)

def get_actions_key(
    account_id: int,
    dataset_id: int,
) -> str:
    return f"edit:{account_id}:{dataset_id}"

def save_action(
    account_id: int,
    dataset_id: int,
    action: dict
):
    key = get_actions_key(
        account_id,
        dataset_id 
    )
    
    client.rpush(
        key,
        json.dumps(action)
    )

def load_actions(
    account_id: int,
    dataset_id: int
) -> list[dict]:
    
    key = get_actions_key(
        account_id,
        dataset_id
    )
    
    actions = client.lrange(
        key,
        0,
        -1
    )
    
    return [
        json.loads(action)
        for action in actions
    ]

def delete_actions(
    account_id: int,
    dataset_id: int
):
    key = get_actions_key(
        account_id,
        dataset_id
    )
    
    client.delete(key)