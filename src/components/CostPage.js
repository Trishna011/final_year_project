import { Box, Heading, Text, Button } from "@chakra-ui/react";
import { motion } from "framer-motion";

const MotionBox = motion(Box);

export default function CostPage({ cost, onRestart, clearAnswers }) {
  
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
      bg="white"
      rounded="2xl"
      shadow="xl"
      textAlign="center"
      maxW="700px"
      color="gray.800"
    >
      <Heading mb={6} color="teal.600">
        🎉 Your Estimated Renovation Cost
      </Heading>

      <Text fontSize="4xl" fontWeight="bold" color="teal.500">
        £{Number(cost || 0).toLocaleString()}
      </Text>


      <Text mt={4} color="gray.600">
        This is an approximate estimate based on your answers.  
        For an accurate quote, please contact our renovation specialists.
      </Text>

      <Button
        mt={8}
        colorScheme="teal"
        rounded="full"
        onClick={handleRestart}
      >
        Start Over
      </Button>
    </MotionBox>
  );
}
