// -*- coding: utf-8 -*-
// A library to display spinorama charts
//
// Copyright (C) 2020-23 Pierre Aubert pierreaubert(at)yahoo(dot)fr
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

/*global Fuse*/
/*eslint no-undef: "error"*/

import { show, hide } from './misc.js';

export function sortMetadata2(metadata, sorter) {
    const sortChildren2 = ({ container, score, reverse }) => {
        // console.log('sorting2 by '+score)
        const items = [...container.keys()];
        if (reverse) {
            items.sort((a, b) => {
                // console.log(score(a), score(b))
                return score(a) - score(b);
            });
        } else {
            items.sort((a, b) => {
                // console.log(score(a), score(b))
                return score(b) - score(a);
            });
        }
        // console.table(items)
        return items;
    };

    function getDateV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        // comparing ints (works because 20210101 is bigger than 20201010)
        if ('review_published' in msr) {
            const reviewPublished = parseInt(msr.review_published);
            if (!isNaN(reviewPublished)) {
                return reviewPublished;
            }
        }
        return 19700101;
    }

    function getPriceV2(key) {
        const spk = metadata.get(key);
        let price = parseFloat(spk.price);
        if (!isNaN(price)) {
            const amount = spk.amount;
            if (amount && amount !== 'each') {
                price /= 2;
                // console.log('getPrice2 each '+price)
            }
            // console.log('getPriceV2 '+price)
            return price;
        }
        // console.log('getPriceV2 noprice')
        return -1;
    }

    function getScoreV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('pref_rating' in msr && 'pref_score' in msr.pref_rating) {
            return spk.measurements[def].pref_rating.pref_score;
        }
        return -10.0;
    }

    function getScoreWsubV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('pref_rating' in msr && 'pref_score_wsub' in msr.pref_rating) {
            return spk.measurements[def].pref_rating.pref_score_wsub;
        }
        return -10.0;
    }

    function getScoreEqV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('pref_rating_eq' in msr && 'pref_score' in msr.pref_rating_eq) {
            return spk.measurements[def].pref_rating_eq.pref_score;
        }
        return -10.0;
    }

    function getScoreEqWsubV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('pref_rating_eq' in msr && 'pref_score_wsub' in msr.pref_rating_eq) {
            return spk.measurements[def].pref_rating_eq.pref_score_wsub;
        }
        return -10.0;
    }

    function getF3V2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('estimates' in msr && 'ref_3dB' in msr.estimates) {
            return -spk.measurements[def].estimates.ref_3dB;
        }
        return -1000;
    }

    function getF6V2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('estimates' in msr && 'ref_6dB' in msr.estimates) {
            return -spk.measurements[def].estimates.ref_6dB;
        }
        return -1000;
    }

    function getFlatnessV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('estimates' in msr && 'ref_band' in msr.estimates) {
            return -spk.measurements[def].estimates.ref_band;
        }
        return -1000;
    }

    function getSensitivityV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('sensitivity' in msr && 'sensitivity_1m' in msr.sensitivity) {
	    return spk.measurements[def].sensitivity.sensitivity_1m;
        }
        return 0.0;
    }

    function getWeightV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('specifications' in msr && 'weight' in msr.specifications) {
            return spk.measurements[def].specifications.weight;
        }
        return 0.0;
    }

    function getSizeWidthV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('specifications' in msr && 'size' in msr.specifications && 'width' in msr.specifications.size) {
            return spk.measurements[def].specifications.size.width;
        }
        return 0.0;
    }

    function getSizeDepthV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('specifications' in msr && 'size' in msr.specifications && 'depth' in msr.specifications.size) {
            return spk.measurements[def].specifications.size.depth;
        }
        return 0.0;
    }

    function getSizeHeightV2(key) {
        const spk = metadata.get(key);
        const def = spk.default_measurement;
        const msr = spk.measurements[def];
        if ('specifications' in msr && 'size' in msr.specifications && 'height' in msr.specifications.size) {
            return spk.measurements[def].specifications.size.height;
        }
        return 0.0;
    }

    function getBrandV2(key) {
        const spk = metadata.get(key);
        return spk.brand + ' ' + spk.model;
    }

    if (sorter.by === 'date') {
        return sortChildren2({
            container: metadata,
            score: (k) => getDateV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'score') {
        return sortChildren2({
            container: metadata,
            score: (k) => getScoreV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'scoreEQ') {
        return sortChildren2({
            container: metadata,
            score: (k) => getScoreEqV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'scoreWSUB') {
        return sortChildren2({
            container: metadata,
            score: (k) => getScoreWsubV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'scoreEQWSUB') {
        return sortChildren2({
            container: metadata,
            score: (k) => getScoreEqWsubV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'price') {
        return sortChildren2({
            container: metadata,
            score: (k) => getPriceV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'f3') {
        return sortChildren2({
            container: metadata,
            score: (k) => getF3V2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'f6') {
        return sortChildren2({
            container: metadata,
            score: (k) => getF6V2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'flatness') {
        return sortChildren2({
            container: metadata,
            score: (k) => getFlatnessV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'sensitivity') {
        return sortChildren2({
            container: metadata,
            score: (k) => getSensitivityV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'brand') {
        return sortChildren2({
            container: metadata,
            score: (k) => getBrandV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'weight') {
        return sortChildren2({
            container: metadata,
            score: (k) => getWeightV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'width') {
        return sortChildren2({
            container: metadata,
            score: (k) => getSizeWidthV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'height') {
        return sortChildren2({
            container: metadata,
            score: (k) => getSizeHeightV2(k),
            reverse: sorter.reverse,
        });
    } else if (sorter.by === 'depth') {
        return sortChildren2({
            container: metadata,
            score: (k) => getSizeDepthV2(k),
            reverse: sorter.reverse,
        });
    } else {
        console.log('ERROR: unknown sorter ' + sorter.by);
    }
}

export function isFiltered(item, filter) {
    let shouldShow = true;
    if (filter.reviewer !== undefined && filter.reviewer !== '') {
        let found = true;
        for (const [name, measurement] of Object.entries(item.measurements)) {
            const origin = measurement.origin.toLowerCase();
            let name2 = name.toLowerCase();
            // not ideal
            name2 = name2
                .replace('misc-', '')
                .replace('-sealed', '')
                .replace('-ported', '')
                .replace('-vertical')
                .replace('-horizontal');
            // console.log('debug: name2=' + name2 + ' origin=' + origin + ' filter.reviewer=' + filter.reviewer)
            if (name2 === filter.reviewer.toLowerCase() || origin === filter.reviewer.toLowerCase()) {
                found = false;
                break;
            }
        }
        if (found) {
            shouldShow = false;
        }
    }
    if (filter.quality !== undefined && filter.quality !== '') {
        let found = true;
        for (const [, measurement] of Object.entries(item.measurements)) {
            const quality = measurement.quality.toLowerCase();
            // console.log('filter.quality=' + filter.quality + ' quality=' + quality)
            if (filter.quality !== '' && quality === filter.quality.toLowerCase()) {
                found = false;
                break;
            }
        }
        if (found) {
            shouldShow = false;
        }
    }
    // console.log('debug: post quality ' + shouldShow)
    if (filter.power !== undefined && filter.power !== '' && item.type !== filter.power) {
        shouldShow = false;
    }
    // console.log('debug: post power ' + shouldShow)
    if (filter.shape !== undefined && filter.shape !== '' && item.shape !== filter.shape) {
        shouldShow = false;
    }
    // console.log('debug: post shape ' + shouldShow)
    if (filter.brand !== undefined && filter.brand !== '' && item.brand.toLowerCase() !== filter.brand.toLowerCase()) {
        shouldShow = false;
    }
    // console.log('debug: post brand ' + shouldShow + 'filter.price=>>>'+filter.price+'<<<')
    if (filter.price !== undefined && filter.price !== '') {
        // console.log('debug: pre price ' + filter.price)
        if (item.price !== '') {
            let price = parseInt(item.price);
            if (item.amount === 'pair') {
                price /= 2.0;
            }
            switch (filter.price) {
                case 'p100':
                    if (price > 100) {
                        shouldShow = false;
                    }
                    break;
                case 'p200':
                    if (price > 200 || price < 100) {
                        shouldShow = false;
                    }
                    break;
                case 'p300':
                    if (price > 300 || price < 200) {
                        shouldShow = false;
                    }
                    break;
                case 'p400':
                    if (price > 400 || price < 300) {
                        shouldShow = false;
                    }
                    break;
                case 'p500':
                    if (price > 500 || price < 400) {
                        shouldShow = false;
                    }
                    break;
                case 'p1000':
                    if (price > 1000 || price < 500) {
                        shouldShow = false;
                    }
                    break;
                case 'p2000':
                    if (price > 2000 || price < 1000) {
                        shouldShow = false;
                    }
                    break;
                case 'p5000':
                    if (price > 5000 || price < 2000) {
                        shouldShow = false;
                    }
                    break;
                case 'p5000p':
                    if (price <= 5000) {
                        shouldShow = false;
                    }
                    break;
            }
        } else {
            // no known price
            shouldShow = false;
        }
        // console.log('debug: post price ' + shouldShow)
    }
    // console.log('debug: post brand ' + shouldShow + 'filter.price=>>>'+filter.priceMin+','+filter.priceMax+'<<<')
    if (
        (filter.priceMin !== undefined && filter.priceMin !== '') ||
        (filter.priceMax !== undefined && filter.priceMax !== '')
    ) {
        var priceMin = parseInt(filter.priceMin);
        if (isNaN(priceMin)) {
            priceMin = -1;
        }
        var priceMax = parseInt(filter.priceMax);
        if (isNaN(priceMax)) {
            priceMax = Number.MAX_SAFE_INTEGER;
        }
        // console.log('debug: pre price ' + filter.price)
        if (item.price !== '') {
            let price = parseInt(item.price);
            if (isNaN(price)) {
                shouldShow = false;
            } else {
                if (item.amount === 'pair') {
                    price /= 2.0;
                }
                if (price > priceMax || price < priceMin) {
                    shouldShow = false;
                }
            }
        } else {
            // no known price
            shouldShow = false;
        }
        // console.log('debug: post price ' + shouldShow)
    }
    return shouldShow;
}

export function isSearch(key, results, minScore, keywords) {
    // console.log('Starting isSearch with key='+key+' minscore='+minScore+' keywords='+keywords);

    let shouldShow = true;
    if (keywords === '' || results === undefined) {
        // console.log('shouldShow is true');
        return shouldShow;
    }

    if (!results.has(key)) {
        // console.log('shouldShow is false (no key '+key+')');
        return false;
    }

    const result = results.get(key);
    const imeta = result.item.speaker;
    const score = result.score;

    if (minScore < Math.pow(10, -15)) {
        const isExact = imeta.model.toLowerCase().includes(keywords.toLowerCase());
        // console.log('isExact ' + isExact + ' model ' + imeta.model.toLowerCase() + ' keywords ' + keywords.toLowerCase());
        // we have an exact match, only shouldShow other exact matches
        if (score >= Math.pow(10, -15) && !isExact) {
            // console.log('filtered out (minscore)' + score);
            shouldShow = false;
        }
    } else {
        // only partial match
        if (score > minScore * 10) {
            // console.log('filtered out (score=' + score + 'minscore=' + minScore + ')');
            shouldShow = false;
        }
        // else { console.log('not filtered out (score=' + score + 'minscore=' + minScore + ')'); }
    }
    return shouldShow;
}

export function process(data, params, printer) {
    const fuse = new Fuse(
        // Fuse take a list not a map
        [...data].map((item) => ({ key: item[0], speaker: item[1] })),
        {
            isCaseSensitive: false,
            matchAllTokens: true,
            findAllMatches: true,
            minMatchCharLength: 2,
            keys: ['speaker.brand', 'speaker.model', 'speaker.type', 'speaker.shape'],
            treshhold: 0.2,
            distance: 10,
            includeScore: true,
            useExtendedSearch: false,
            shouldSort: true,
        }
    );
    const fragment = new DocumentFragment();
    const sorter = params[0];
    const filters = params[1];
    const keywords = params[2];
    let results;
    let minScore = 1;
    if (keywords !== '') {
        results = fuse.search(keywords);
        // console.log('searching with keywords: '+keywords+' #matches: '+results.length);
        if (results.length > 0) {
            // minScore
            for (const spk in results) {
                if (results[spk].score < minScore) {
                    minScore = results[spk].score;
                }
            }
        }
        results = new Map(results.map((obj) => [obj.item.key, obj]));
    }

    sortMetadata2(data, sorter).forEach((key, index) => {
        const speaker = data.get(key);
        const testFiltered = isFiltered(speaker, filters);
        const testKeywords = isSearch(key, results, minScore, keywords);
        const currentFragment = printer(key, index, speaker);
        if (testFiltered && testKeywords) {
            show(currentFragment);
        } else {
            hide(currentFragment);
        }
        fragment.appendChild(currentFragment);
    });
    return fragment;
}
