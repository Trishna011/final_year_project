const React = require('react')

const STRIP = new Set([
  'colorScheme','variant','rounded','shadow','textAlign','maxW','maxH',
  'minW','minH','w','h','p','px','py','pt','pb','pl','pr','mt','mb','ml',
  'mr','mx','my','m','spacing','columns','overflowY','overflow','bg','color',
  'borderWidth','borderColor','focusBorderColor','fontSize','fontWeight',
  'letterSpacing','display','alignItems','justifyContent','position','top',
  'left','zIndex','lineHeight','whiteSpace','cursor','size','sx',
  '_hover','_focus','_focusVisible','_active','_disabled','_placeholder',
  'isInvalid','isDisabled','isRequired','isReadOnly','isFullWidth',
  'bgGradient','gap','flex','flexDir','flexDirection','transition','transform',
  'whileHover','whileTap','isTruncated','noOfLines','layerStyle','textStyle',
  'initial','animate','exit',
])

function clean(props) {
  const out = {}
  for (const [k, v] of Object.entries(props)) {
    if (!STRIP.has(k)) out[k] = v
  }
  return out
}

const motion = (Component) => {
  return function MotionWrapper({ children, ...props }) {
    return React.createElement(Component, clean(props), children)
  }
}

const AnimatePresence = ({ children }) => children

module.exports = { motion, AnimatePresence }