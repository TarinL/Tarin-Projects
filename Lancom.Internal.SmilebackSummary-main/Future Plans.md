# Future Plans 

## Potential changes
1. Integrating with ChatGPT or Copilot to provide sentiment analysis of comments from surveys. 
3. Any common problems identified
4. Action from staff to follow up on bad reviews.

## AI sentiment analysis
> This would be a part of the monthly Smileback Email only.

### ChatGPT-4
Using chatGPT this is an example of how sentiment analysis could be used on the comments received from the Smileback surveys. This is done using the OpenAI SDK. 

```javascript
import OpenAI from "openai";

const client = new OpenAI({
    apiKey: "YOUR_API_KEY"
});

const model = "gpt-4o";
const temperature = 0.3;
const message = [
    {
        "role": "system",
        "content": "Act as a highly experienced analyst with expertise in sentiment analysis. Analyse all the comments given to you and return a 'score': an overall sentiment rating from 0 (very negative) to 10 (very positive) that reflects the overall sentiment of the comments. You will also return a 'summary': a summary of maximum 150 words where you will identify and report key concerns, common problems and/or praises mentioned in all the comments. Give your analysis in JSON format { 'score': 0, 'summary': 'overall summary' }."
    },
    {
        "role": "user",
        "content": `Analyze the sentiment of these customer comments: ${comments}`  

  }
];

async function sentimentAnalysis(comments) {
    const response = await client.chat.completions.create({
        model: model,
        messages: message,
        temperature: temperature,
    });

    return response.choices[0].message.content;
}

// example usage
const analysis = sentimentAnalysis(comments);
const score =  analysis.score;
const summary = analysis.summary;

// example output 

{
  "score": 5,
  "summary": "Customer feedback is mixed, with many users praising quick resolutions, knowledgeable staff, and professional service. However, common frustrations include slow response times, repeated escalations, and incomplete issue resolution, leading to dissatisfaction among some customers. While many had positive experiences, improving consistency in response speed and problem resolution could enhance overall satisfaction."
}
```
### Amazon Bedrock 
AWS offers Amazon Bedrock which is a service with multiple LLM's that you can use. For this example 

## Pricing 
> All pricing as of Feb 4 2025

Pricing for chatGPT and Amazon Bedrock operate on a per token basis. 
The average number of tokens for a comment is `16.644`. This is calculated by `average number of characters / 4`.
The average number of reviews per month from Jan 2024 to Jan 2025 is 134.08.
Therefore, the average number of input tokens is `134.08 * 16.644 = 2231.62752`
The maximum number of output tokens would be `37.5`. Using the same calculation. 

**GPT-4**

chatGPT-4 charges `$0.03/thousand input tokens` and `$0.06/thousand output tokens` so the total cost for processing `2,231.62752` input tokens and `37.5` output tokens with GPT-4 is approximately `$0.0692 USD` per month.

**Amazon Titan Text Lite**

Amazon Titan Text Lite charges `$0.0002/thousand input tokens` and `$0.00025/ thousand output tokens` so the total cost for processing `2,231.62752` input tokens and `37.5` output tokens with Amazon Titan Text Lite is approximately `$0.0004557 AUD` per month.


