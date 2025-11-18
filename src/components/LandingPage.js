import { Box, Button, Text } from "@chakra-ui/react";

export default function LandingPage({ onStart }) {
  return (
    <Box
      p={10}
      bg="whiteAlpha.100"
      rounded="2xl"
      shadow="2xl"
      textAlign="center"
      color="white"
    >
      <Text mb={8} fontSize="2xl" fontWeight="semibold" color={"blackAlpha.800"}>
        🏡 Property Renovation Calculator
      </Text>
      <Button
        size="lg"
        rounded="full"
        colorScheme="teal"
        px={8}
        onClick={onStart}
        _hover={{
          transform: "scale(1.05)",
          boxShadow: "lg",
        }}
      >
        Start Here
      </Button>
    </Box>
  );
}
