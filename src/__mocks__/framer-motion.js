const React = require('react')

// motion needs to be a function that accepts a component and returns it
const motion = (component) => {
  return ({ children, ...props }) => React.createElement(component, props, children)
}

const AnimatePresence = ({ children }) => children

module.exports = { motion, AnimatePresence }