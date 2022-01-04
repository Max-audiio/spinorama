import metadata from './metadata.js'
import { byScore } from './sort.js'
import { toggleId, getID, getPicture, getLoading, getDecoding, getField, getReviews } from './misc.js'

function getSpider (brand, model) {
  // console.log(brand + model);
  return encodeURI(brand + ' ' + model + '/spider.jpg')
}

function getContext (key, value) {
  // console.log(getReviews(value));
  const scores = getField(value, 'pref_rating', value.default_measurement)
  scores.pref_score = parseFloat(scores.pref_score).toFixed(1)
  scores.pref_score_wsub = parseFloat(scores.pref_score_wsub).toFixed(1)
  const scoresEq = getField(value, 'pref_rating_eq', value.default_measurement)
  scoresEq.pref_score = parseFloat(scoresEq.pref_score).toFixed(1)
  scoresEq.pref_score_wsub = parseFloat(scoresEq.pref_score_wsub).toFixed(1)
  return {
    id: getID(value.brand, value.model),
    brand: value.brand,
    model: value.model,
    sensitivity: value.sensitivity,
    estimates: getField(value, 'estimates', value.default_measurement),
    estimatesEq: getField(value, 'estimates_eq', value.default_measurement),
    scores: scores,
    scoresEq: scoresEq,
    reviews: getReviews(value),
    img: {
      // avif: getPicture(value.brand, value.model, "avif"),
      webp: getPicture(value.brand, value.model, 'webp'),
      jpg: getPicture(value.brand, value.model, 'jpg'),
      loading: getLoading(key),
      decoding: getDecoding(key)
    },
    spider: getSpider(value.brand, value.model)
  }
}

Handlebars.registerHelper('isNaN', function (value) {
  return isNaN(value)
})

const source = document.querySelector('#scoresht').innerHTML
const template = Handlebars.compile(source)

function printScore (key, value) {
  const context = getContext(key, value)
  const html = template(context)
  const divScore = document.createElement('div')
  divScore.setAttribute('id', context.id)
  divScore.setAttribute('class', 'column py-0 is-12 is-vertical')
  divScore.innerHTML = html
  const button = divScore.querySelector('#' + context.id + '-button')
  button.addEventListener('click', e => toggleId('#' + context.id + '-details'))
  return divScore
}

export function display () {
  const speakerContainer = document.querySelector('[data-num="0"')
  const fragment1 = new DocumentFragment()

  byScore.forEach(function (value, key) {
    const speaker = metadata[value]
    fragment1.appendChild(printScore(value, speaker))
  })
  speakerContainer.appendChild(fragment1)
}
