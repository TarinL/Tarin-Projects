const RATINGS = {
    "1": "positive",
    "0": "neutral",
    "-1": "negative"
}

/**
 * Checks if review is within a time period specified by an offset.
 * @param review - single review, JSON format
 * @param offset - integer representing the amount of days
 * @returns {boolean}
 * @private
 */
function _isValidDate(review, offset) {
    const currentDate = new Date();
    const reviewDate = new Date(review["rated_on"]);
    return currentDate - reviewDate <= (offset * 86400000);
}

/**
 * checks if review has been deleted and is within date range.
 * @param review - Single review, JSON format.
 * @param offset - integer number representing number of days
 * Assumes pre-validated data
 * @returns {boolean}
 * @private
 */
function isValidReview(review, offset) {
    return review["status"] !== "deleted" && _isValidDate(review, offset);
}

/**
 * Validates data and throws an exception if not valid.
 * @param content
 */
function assertValidData(content) {
    if (content === null) {
        throw new Error("Data is null!");
    }
    else if (content === undefined) {
        throw new Error("Data is undefined!");
    }
    else if (content.length <= 0) {
        throw new Error("No data exists!");
    }
    else if (content.constructor !== ({}).constructor) {
        throw new Error("Not JSON data!")
    }
    else if (!content["results"]) {
        throw new Error("Data is not formatted correctly! No results list.")
    }
    else return true;
}

/**
 * Selects reviews with comments and sorts the comments into dictionary with positive, negative and neutral keys
 * @param reviews - array of reviews, JSON format.
 * Assumes pre-validated data
 * @returns {dict[positive: [{}], negative: [{}], neutral: [{}]]}. list of dicts.
 */
function processComments(reviews) {
    return reviews
        .filter((review) => review["comment"] != null && review.contact != null) // checks both null and undefined
        .reduce((output, review) => {
            let comment = {
                "comment": review["comment"], 
                "agents": review["ticket"]["agents"],
                "name": review["contact"]["name"],
                "company": review["company"]["name"]
            }
            output[RATINGS[review["rating"]]].push(comment);
            return output;
        }, {"positive": [], "neutral": [], "negative": []});
}

/**
 * Creates a dictionary with a name: int[].
 * The int[] has a score and a tally for total reviews. Score is calculated
 * by adding the rating of a review.
 * @param reviews - array of reviews, JSON format.
 * Assumes pre-validated data
 * @returns {dict[string: dict[string: int]]}
 * @private
 */
function _sumIndividualRatings(reviews) {
    return reviews.reduce((agentRatingsDict, review) => {
        const rating = review["rating"];
        const names = review["ticket"]["agents"];
        names.forEach(name => {
            if (name in agentRatingsDict) {
                agentRatingsDict[name].score += rating;
                agentRatingsDict[name].count += 1;
            } else {
                agentRatingsDict[name] = { score: rating, count: 1 };
            }
        });
        return agentRatingsDict;
    }, {});
}

/**
 * Calculates the CSAT score per agent using the formula [(individual rating / total number of reviews) * 100] refer to
 * [docs](../SmilebackDataDocumentation.md) for more info
 * @param reviews - array of reviews, JSON format.
 * Assumes pre-validated data
 * @returns {dict[string: int]}
 */
function calculateIndividualCsatScores(reviews) {
    const agentRatingsDict = _sumIndividualRatings(reviews);
    return Object.fromEntries(Object.entries(agentRatingsDict).map(
        ([name, {score, count}]) => [name, {score: Math.round((score / count) * 100), total: count}]
    ));
}

/**
 * calculates the Net CSAT score by averaging the individual CSAT scores.
 * @param reviews - array of reviews, JSON format.
 * Assumes pre-validated data
 * @returns {number}
 */
function calculateNetCsatScore(reviews) {
    let total = reviews.length;
    if (total === 0) { return 0; } 
    const tally = reviews.reduce((total, review) => total + review["rating"], 0)
    return {"score": ((tally/total) * 100).toFixed(2), "total": total};
}

/**s
 * Calculates number of happy, sad, and neutral faces.
 * Uses ratings dict at top of file.
 * @param reviews - array of reviews, JSON format.
 * Assumes pre-validated data
 * @returns {dict[happy: number, sad: number, neutral: number]}
 * @private
 */
function _countFaces(reviews) {
    return reviews
        .reduce((countFacesDict, review) => {
            countFacesDict[RATINGS[review["rating"]]] += 1;
            return countFacesDict;
        }, {"positive": 0, "neutral": 0, "negative": 0});
}

/**
 * Calculates the percentage of happy, sad, and neutral faces.
 * @param reviews - array of reviews, JSON format.
 * Assumes pre-validated data
 * @returns {dict[happy: number, sad: number, neutral: number]}
 */
function calculateFacesPercentages(reviews) {
    if (reviews.length === 0) { return 0; }
    const faces = _countFaces(reviews);
    faces["positive"] = {"score": ((faces["positive"] / reviews.length) * 100).toFixed(2), "total": faces["positive"]};  
    faces["neutral"] = {"score": ((faces["neutral"] / reviews.length) * 100).toFixed(2), "total": faces["neutral"]};
    faces["negative"] = {"score": ((faces["negative"] / reviews.length) * 100).toFixed(2), "total": faces["negative"]};
    return faces;
}

/**
 * calculates the number of positive, neutral and negative faces for each agent.
 * @param reviews - array of reviews, JSON format.
 * @returns {dict[string: dict[string: int]]}
 */
function _sumIndividualFaces(reviews) {
    return reviews.reduce((agentRatingsDict, review) => {
        const rating = review["rating"];
        const names = review["ticket"]["agents"];
        names.forEach(name => {
            if (false === (name in agentRatingsDict)) {
                agentRatingsDict[name] = { "positive": 0, "neutral": 0, "negative": 0 };
            }
            agentRatingsDict[name][RATINGS[rating]] += 1;
        });
        return agentRatingsDict;
    }, {});
}

/**
 * calculates the percentage of positive, neutral and negative faces for each agent.
 * @param {Object} reviews - array of reviews, JSON format. 
 * @returns {[String: {positive: int, neutral: int, negative: int}]}
 */
function calculateIndividualFacesPercentages(reviews) {
    const agentRatingsDict = _sumIndividualFaces(reviews);
    return Object.fromEntries(Object.entries(agentRatingsDict).map(
        ([name, {positive, neutral, negative}]) => {
            const total = positive + neutral + negative;
            if (total === 0) {
                return [name, {
                    positive: 0,
                    neutral: 0,
                    negative: 0
                }];              
            } else {
                return [name, {
                    positive: ((positive / total) * 100).toFixed(2),
                    neutral: ((neutral / total) * 100).toFixed(2),
                    negative: ((negative / total) * 100).toFixed(2)
                }];
            }
        } 
    )); 
}

/**
 * Sorts and calculates the top three agents based on their CSAT score and secondarily by total number of reviews.
 * @param {Object} reviews 
 * @returns [[String, {score: int, total: int}]]
 */
function calculateTopThreeAgents(reviews) {
    const csatScores = calculateIndividualCsatScores(reviews);
    const sortedCsatScores = Object.entries(csatScores).sort((a, b) => b[1]["score"] - a[1]["score"] || b[1]["total"] - a[1]["total"]);
    return sortedCsatScores.slice(0, 3);
}

/**
 * Calculates the running score of companies and the total number of reviews.
 * @param {Object} reviews - JSON object
 * @returns {String: {score: int, total: int}}
 */
function _calculateReviewsCompanies(reviews) {
    return reviews
        .reduce((companies, review) => {
            if ((review["company"])) {
                const company = review["company"]["name"];
                const rating = review["rating"];
                if (false === (company in companies)) {
                    companies[company] = { "score": 0, "total": 0 };
                }
                companies[company]["score"] += rating;
                companies[company]["total"] += 1;
            }
            return companies;
        }, {});
}

/**
 * calculates the CSAT score for each company
 * @param {Object} reviews - JSON object
 * @returns [[Company, {score: int, total: int}]]
 */
function calculateCompanyCsatScores (reviews) {
    const companiesScoreDict = _calculateReviewsCompanies(reviews);
    return Object.fromEntries(Object.entries(companiesScoreDict)
        .map(([company, {score, total}]) => [company, {score: ((score / total) * 100).toFixed(2), total: total}]
    ));
}

/**
 * calculates the top 5 and worst 5 companies based on CSAT score and total number of reviews.
 * @param {Object} reviews - JSON object 
 * @returns {"best": {String: {score: int, total: int}}, "worst": {String: {score: int, total: int}}}
 */
function bestWorstFiveCompanies(reviews) {
    let companyScores = calculateCompanyCsatScores(reviews);
    const sortedCompanies = Object.entries(companyScores).sort((a, b) => b[1]["score"] - a[1]["score"] || b[1]["total"] - a[1]["total"]);
    const a = Object.entries(companyScores);
    const best = Object.fromEntries(sortedCompanies.slice(0,5));
    const worst = Object.fromEntries(sortedCompanies.slice(-5).reverse());
    return {"best": best, "worst": worst};
}

/**
 * calculates the top three commenters based on the number of comments they have made.
 * @param {Object} reviews - JSON Object 
 * @returns  {"positive": {}, "neutral": {}, "negative": {}} 
 */
function calculateTopThreeCommenters(reviews) {
    const groupedReviews = reviews
        .filter(review => review["contact"] != null)
        .reduce((output, review) => {
            const rating = RATINGS[review["rating"]];
            const name = review["contact"]["name"];
            if (false === (name in output[rating])) {
                output[rating][name] = 0;
            }
            output[rating][name] += 1;
            return output;
        }, {"positive": {}, "neutral": {}, "negative": {}});

    const sortedReviews = Object.entries(groupedReviews).reduce((prev, [rating, names]) => {
        prev[rating] = Object.entries(names)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3)
            .map(([name, total]) => ({name, total}));
        return prev;
    }, {});
    return sortedReviews;
}

export { calculateFacesPercentages, calculateNetCsatScore, processComments, calculateIndividualCsatScores,
    isValidReview, assertValidData, calculateIndividualFacesPercentages, calculateTopThreeAgents, bestWorstFiveCompanies, 
calculateTopThreeCommenters };

