// function that hits smileback api and returns data
import { smilebackConfig } from './config.mjs';


/**
 * makes the call to an api
 * @param url - base url 'https://app.smileback.io'
 * @param options - Method 'GET' and Authorization header
 * @returns {Promise<Object>} JSON object
 * @private
 */
async function _fetchApi(url, options) {
    const response = await fetch(url, options);
    if (response.ok) {
        return await response.json();
    } else {
        const body = await response.text();
        throw new Error(`${response.statusText}\n${body}`);
    }
}

/**
 * creates form data for the token api call
 * @returns {FormData}
 * @private
 */
function _createTokenFormData() {
    const formData = new FormData();
    formData.append("grant_type", "password");
    formData.append("scope", "read read_recent");
    formData.append("username", smilebackConfig.email);
    formData.append("password", smilebackConfig.password);
    return formData
}
/**
 * returns header for token api call
 * @returns {header}
 */
function _createTokenAuthHeader() {
    const header = new Headers();
    const encodedPair = btoa(`${smilebackConfig.clientId}:${smilebackConfig.secret}`);
    header.append('Authorization', `Basic ${encodedPair}`);
    return header;
}

/**
 * fetches authentication token from smileback
 * @returns {Promise<String>}
 * @private
 */
async function _getSmilebackToken () {
    const url = `${smilebackConfig.url}/api/token/`;
    const options = {
        body: _createTokenFormData(),
        method: 'POST',
        headers: _createTokenAuthHeader()
    }
    return _fetchApi(url, options);
}

/**
 * fetches data from smileback api from a specified date to now
 * @param date - in the form YYYY-MM-DD
 * @returns {Promise<Object>}
 * @private
 */
async function _getApiData(date) {
    let month = date.getMonth() + 1;
    let day = date.getDate(); 
    
    if (date.getMonth() < 10) {
        month = `0${month}`;
    }
    if (date.getDate() < 10) {
        day = `0${day}`;
    }
    const dateString = `${date.getFullYear()}-${month}-${day}`;
    const token = await _getSmilebackToken();
    const header = new Headers();
    header.append('Authorization',  `${token["token_type"]} ${token["access_token"]}`);
    const url = `${smilebackConfig.url}/api/v3/reviews/?modified_since=${dateString}`;
    console.log(`${smilebackConfig.url}/api/v3/reviews/?modified_since=${dateString}`);
    const options = {
        method: 'GET',
        headers: header
    }
    return _fetchApi(url, options);
}

/**
 * calculates how many days are in the current month.
 * @returns {number}
 * @private
 */
function _calculateDaysInMonth() {
    const daysOfMonths = {'1': 31, '2': 29, '3': 31, '4': 30, '5': 31, '6': 30, '7': 31,
        '8': 31, '9': 30, '10': 31, '11': 30, '12': 31}
    let date = new Date();
    return daysOfMonths[date.getMonth() + 1];
}

/**
 * gets review data  modified in the last month.
 * @returns {Promise<Object|undefined>}
 */
async function getMonthlyReviewData() {
    let date = new Date();
    if (date.getMonth() === 0) {
        date.setFullYear(date.getFullYear() - 1);
        date.setMonth(11);
    }
    else {
        date.setMonth(date.getMonth() - 1);
    }
    return await _getApiData(date)
}

/**
 * gets review data modified in the past week.
 * @returns {Promise<Object|undefined>}
 */
async function getWeeklyReviewData() {
    let date = new Date();
    date.setDate(date.getDate() - 7);
    return await _getApiData(date);
}

export {getWeeklyReviewData, getMonthlyReviewData}



