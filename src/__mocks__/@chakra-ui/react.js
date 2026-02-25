const React = require('react')

const Box = ({ children, as: Tag = 'div', onChange, value, ...rest }) =>
  React.createElement(Tag, { onChange, value, ...rest }, children)

const Button = ({ children, onClick, ...rest }) =>
  React.createElement(
    'button',
    {
      onClick: typeof onClick === 'function' ? onClick : undefined,
      ...rest,
    },
    children
  )

const Heading = ({ children }) => React.createElement('h1', null, children)

const Text = ({ children }) => React.createElement('p', null, children)

const VStack = ({ children }) => React.createElement('div', null, children)

const SimpleGrid = ({ children }) => React.createElement('div', null, children)

const Input = ({onChange, value, placeholder, type, min,
...rest
}) =>
React.createElement('input', { onChange, value, placeholder, type, min,
...rest
})

const Field = {
  Root: ({ children }) => React.createElement('div', null, children)
}

module.exports = { Box, Button, Heading, Text, VStack, SimpleGrid, Input, Field }