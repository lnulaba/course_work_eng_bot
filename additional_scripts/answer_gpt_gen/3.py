from openai import OpenAI

api_keys = {
    "my": "6bd60986ac8544d08311d5f0a1736393",
    "github1": "f0af93f61ad44ceeb26a4aca6be8e75c",
    "github2": "aa4c891e0d7d4491a919859bbb33b4b4",
    "github3": "74b0c0abd2294719ba29967c27bde367",
    "github4": "a7caa007814440618e14d45e42bd5450",
    "github5": "0710951b319a4cd79e155a8e40413658",
    "github6": "7ae3a9a75e99458cb771a2e52134e8cb",
    "github7": "09c8c09c82764e73a906a8f353115bec",
    "github8": "8df72ab4814643ca897ee213f4d2b054",
    "github9": "afd78080d3314927bc2d9ffc44ae6215",
    "github10": "05eaba6dd95047d4bb17657d26f71cac",
    "github11": "a4e0c569dfe04440a9dc81720921d809",
    "github12": "8b10e507d0ae4eeb9c591d3da3273e22",
    "github13": "748552329098444c9830a0b60ce48373",
    "github14": "417c93a52af34fe985efe1c9bfbb5a06"
}

client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key=api_keys["my"],
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "say hello ukrainian"}],
)

print(response.choices[0].message.content)