# SmileBack Data Replication API

## API Version: 3.3 (/api/v3/)
### Link to full documentation:  
``` javascript
https://docs.connectwise.com/@api/deki/files/47834/SmileBack_Data_Replication_API_-_v3.3_2024.pdf?revision=1
```

## Introduction

### Who is this API for?
This API is specifically designed for business intelligence and reporting solutions that want to replicate a customer’s SmileBack dataset into their internal storage systems for further analysis and then keep those two datasets in sync.

### What does this API offer?
The SmileBack Data Replication API offers the BI/reporting solution full access to a customer’s dataset of reviews. Special focus is given to making incremental synchronisation as fast and efficient as possible on both ends. This API is purely read-only. The customer has full control over granting and revoking the API consumer’s right to access their dataset.

---

## Glossary

- **Customer**: An organisation using SmileBack to collect feedback on their service tickets. Taking the role of the ‘Resource Owner’ in OAuth 2.0.
- **Integrator**: An organisation offering a business intelligence and reporting solution to customers. These are the direct API consumers and the main audience of this document. Taking the role of ‘Client’ in the OAuth 2.0 flow.
- **End User**: The person providing feedback to the Customer. Usually the Customer’s client.
- **Ticketing System**: The system the Customer uses to manage (receive, update) tickets.
- **Rating**: The nature of the Review the End User is leaving on the Ticket: positive, neutral, or negative.
- **Review (or CSAT Review)**: The core entity of Customer Satisfaction feedback engine on SmileBack. References a single Ticket and consists of Rating, Comment (optional), Ticket Details, and any additional data the Customer might have provided (e.g., tags).
- **Capturing**: The process of asking an End User for their Rating and Comment on a specific Ticket.
- **To Rate**: The act of providing a rating and comment on a Ticket by the End User.
- **NPS Responses**: Feedback captured via SmileBack application for a specific NPS Campaign of a Customer, typically consisting of a numeric score and an optional comment.
- **Campaign**: An NPS survey sent by the Customer to measure loyalty to their company, brand, product, or service.
- **Score**: The numeric part of feedback in NPS surveys (0 to 10).
- **Project Survey**: A survey configured by the Customer within SmileBack to be triggered based on specific Project or Phase status changes in their PSA instance.

---

## SmileBack Replication API Design & Usage

### Concepts
This API is designed to allow an integration to store a local mirrored copy of a Customer’s SmileBack dataset (“replication”) and keep it in sync with changes. This includes:
- Newly captured reviews.
- Retroactive changes (e.g., tagging, notes, or metadata updates).

### Data Pulling - Incremental Updates Concept (IMPORTANT)
The Replication API transfers only data that has changed since the last sync using the `last_modified` timestamp.

#### Key Aspects:
- Use the `modified_since` filter on `/api/v3/reviews/` to request reviews changed since the last update.
- Initial Sync:
  - Fetch the entire dataset when the integration is first set up.
  - Use repeated calls with updated `modified_since` until no more reviews are returned.
- Incremental Sync:
  - Regularly update your dataset using the `modified_since` filter with the last `last_modified` timestamp.
  - Repeat calls if the `next` field in the result is not null, ensuring no data is missed.

### CSAT Review Lifecycle

Two types of CSAT reviews:
1. Rated: End User has rated (non-null `rating` and `rated_on` values).
2. Unrated: Exists but has no feedback (`rating` and `rated_on` are null).

Fields like `status`, `tags`, `contact`, `company`, and `ticket` can change at any point. Deleted reviews must be removed from the replicated dataset when marked as `status: deleted`.

---

## CSAT Response Rate Calculation
The response rate is calculated as the ratio of rated reviews (`rating != null`) to all reviews in a given time interval. To fetch unrated reviews for calculation, set the `include_unrated` parameter to `true` in the API request.

## CSAT Score Calculation
Net CSAT Score is calculated as follows:
- Assign scores: 100 (positive), 0 (neutral), -100 (negative).
- Average the scores:
  ```
  (Sum of scores) / (Number of rated reviews)
  ```
  Example: Positive (100), Neutral (0), Negative (-100), Positive (100)
  ```
  (100 + 0 - 100 + 100) / 4 = 25
  ```

---

## Authentication

### Overview
SmileBack uses OAuth 2.0 for authentication and authorisation, giving Customers full control over data access.

### User Control
- Any SmileBack user with ‘Account Administrative’ privileges can grant or revoke API access.

### Scopes
- The only available scope is `read` for full read-only access to the Customer’s dataset.

### Authentication Endpoints (Production Environment)
1. **Token Request**:
   ```
   https://app.smileback.io/api/token/
   ```
   `Body` as formdata:
   - `grant_type`: `password` .
   - `scope`: `read read_recent`.
   - `username`: account `email`.
   - `password`: account `password`.
   
   `method`: 'POST'
   
   `Headers`:
   - `Authorization`: `Basic {encoded pair}` 
      - encoded pair =`btoa (clintID:secret)`
2. **Data Access**
    The Data Replication API offers dedicated endpoints but all start with this url:
    ```plaintext
    GET https://<api_base_url>/v3/
    ```
    Must include this `Header`:
    - `Authorization`: `token_type`: `access_token`

    #### Accessed from token
    ```plaintext
    token["token_type]
    token["access_token"]
    ```

## Data Access (CSAT Reviews)

### Overview
The Data Replication API offers a dedicated endpoint:
```plaintext
GET https://<api_base_url>/v3/reviews/
```

### Filtering
| Parameter Name | Data Type | Description |
|---|---|---|
| `modified_since` | `timestamp with timezone` | Returns reviews modified since the given timestamp. |
| `include_unrated` | `boolean` (optional) | Includes reviews without ratings if `true` (default is `false`). |
| `limit` | `integer` (optional) | Specifies the maximum number of reviews returned (cannot exceed page size).|

### Response Format
The response is a JSON object containing the following structure:
```json
{
    "count": 42,
    "previous": null,
    "next": "https://<api_base_url>/v3/reviews/?limit=2&offset=2",
    "results": [
        { ... },
        { ... }
    ]
}
```
- **count**: Total number of reviews matching the filters.
- **previous**: URL for the previous page (null if first page).
- **next**: URL for the next page (null if last page).
- **results**: Array of review objects.

**Example of a single Smileback review**.

```json
{
  id: 35929235,
  rating: 1,
  comment: 'quick fix, thanks',
  ticket: {
    id: '2864851',
    title: 'SL report issue',
    segment: { id: '1', name: 'Engineering' },
    agents: [ 'AshK', 'NiamhF' ],
    closed_on: '2024-12-12T01:32:42Z'
  },
  contact: { id: '2522', name: 'John Doe', email: 'johndoe@missing.nz' },
  company: {
    id: '500',
    name: 'Missing NZ',
    territory_name: 'New Zealand',
    territory_remote_id: '2',
    market_name: 'Manufacturing',
    market_remote_id: '14'
  },
  status: 'open',
  tags: [],
  has_marketing_permission: false,
  viewed_on: null,
  rated_on: '2024-12-12T01:48:29.627972Z',
  permalink: 'https://app.smileback.io/reviews/2864851/',
  last_modified: '2024-12-12T01:48:58.533361Z'
}
```

### Review Entity Format
Each review object contains the following fields:
| Field Name | Data Type | Description |
|---|---|---|
| `id` | `integer` | Unique identifier for the review in SmileBack. |
| `rating` | `integer` | Rating: 1 (positive), 0 (neutral), -1 (negative), or `null` (unrated). |
| `comment` | `string` | Optional comment provided by the end user. |
| `ticket.id` | `string` | Ticket ID from the ticketing system. |
| `ticket.title` | `string` | Optional title/summary of the ticket. |
| `ticket.closed_on` | `timestamp` | Date when the ticket was closed in the system. |
| `contact.email` | `string` | Email address of the contact associated with the ticket. |
| `status` | `string` | Status of the review: `open`, `done`, or `deleted`. |
| `tags` | `list` | List of tags assigned to the review. |
| `last_modified` | `timestamp` | Timestamp of the last modification to the review. |
| `ticket.agents` | `list` of strings | List of agents the ticket is associated with. |

All timestamps are in ISO8601 format and use UTC.

---

## Processing Review Data

### Overview
The review data processing workflow involves multiple steps to organise, categorise, and analyse the collected feedback. This enables actionable insights and improved reporting capabilities. Below are the main steps:

1. **Categorising Comments**:
   - Reviews with comments are extracted and grouped based on their ratings into positive, neutral, or negative categories. This allows for easier sentiment analysis and review management. They are stored in a dictionary with keys positive, negative, and neutral. `Expected output example`: 
   ```javascript
   {
    positive: [
    'quick fix, thanks',
    'Very fast resolution, thank you!!!',
    'Great job'
    ]
    negative: [
    "My client still can't access power BI which i raised a ticket 3 weeks ago",
    'Nothing changed compared to what it was when this ticket was first raised'
    ]
    neutral: [
       'Whilst the support when I got it was good and Stuart resolved my issue, it took nearly 40 minutes to make contact with anyone on the helpdesk either via the button or via directly calling the helpdesk.',
      "Thank you but we didn't create this ticket and I have no idea what it means."
    ]
   }
   ```

2. **Calculating Individual CSAT Scores**:
   - Each review is associated with agents responsible for the ticket. The ratings are summed per agent to calculate their individual Customer Satisfaction (CSAT) scores. See [CSAT Score Calculation](#csat-score-calculation) for more info on the calculation. The scores are stored in a dictionary with names as keys and a number that is their CSAT score. `Expected output example`:
   ```javascript
   {
    BenD: 96,
    MikeH: 69,
    DixieN: 100
   }
   ```

3. **Deriving Net CSAT Score**:
   - The individual CSAT scores of all agents are averaged to produce a Net CSAT score. This metric provides an overall indication of customer satisfaction for the business. See [CSAT Score Calculation](#csat-score-calculation) for more info on the calculation. The is simply a number between -100 and 100.  

4. **Face Percentages**:
   - The reviews are analysed to calculate the percentage of happy, neutral, and sad responses. These percentages give a quick overview of customer sentiment. This is calculated with the formula: 
   ```plaintext
   (number of happy faces / total number of faces) * 100
   ```
   This is stored in a dictionary with happy, neutral and sad as keys with a number between 0 and 100 as the value representing the percentage. `Expected output example`:
   ```javascript
   { happy: 96.8, neutral: 1.52, sad: 1.68 }
   ```

5. **Response Rate**:
   - The total percentage of reviews completed is reported. This tracks participation and overall survey coverage.

