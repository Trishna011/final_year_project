import { Box, Heading, Text, Button, VStack } from "@chakra-ui/react";
import { motion } from "framer-motion";

const MotionBox = motion(Box);

export default function CostPage({ cost, postRenovationValue, onRestart, clearAnswers }) {
  const handleRestart = () => {
    clearAnswers();
    onRestart();
  };

  return (
    <MotionBox
      key="result"
      initial={{ opacity: 0, y: 80 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -80 }}
      transition={{ duration: 0.8, ease: "easeInOut" }}
      p={8}
      bg="transparent"
      textAlign="center"
      maxW="700px"
      w="100%"
    >
      <VStack spacing={6}>
        {/* Renovation cost card */}
        <Box
          bg="white"
          rounded="2xl"
          shadow="xl"
          p={8}
          w="100%"
        >
          <Heading mb={4} color="teal.600">
            🎉 Your Estimated Renovation Cost
          </Heading>

          <Text fontSize="4xl" fontWeight="bold" color="teal.500">
            £{Number(cost || 0).toLocaleString()}
          </Text>

          <Text mt={4} color="gray.600">
            This is an approximate estimate based on your answers.
          </Text>
        </Box>

        {/* Post renovation value card */}
        <Box
          bg="white"
          rounded="2xl"
          shadow="xl"
          p={8}
          w="100%"
        >
          <Heading mb={4} color="teal.600">
            🎉 Estimated Property Value After Renovation
          </Heading>

          <Text fontSize="4xl" fontWeight="bold" color="teal.500">
            £{Number(postRenovationValue || 0).toLocaleString()}
          </Text>

          <Text mt={4} color="gray.600">
            This is an approximate estimate based on your answers.
          </Text>
        </Box>

        <Button
          mt={4}
          colorScheme="teal"
          rounded="full"
          onClick={handleRestart}
        >
          Start Over
        </Button>
      </VStack>
    </MotionBox>
  );
}
