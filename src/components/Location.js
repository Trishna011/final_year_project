import { Box, Button, Heading } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function Location({ onBack, onNext, answers }) {
  const [selectedOption, setSelectedOption] = useState("");

  const options = [
    "Manchester City Centre", "Salford", "Stockport", "Bolton", "Bury", "Oldham",
    "Rochdale", "Tameside", "Trafford", "Wigan", "Altrincham",
    "Ashton-under-Lyne", "Prestwich", "Didsbury", "Chorlton", "Withington",
    "Levenshulme", "Sale", "Stretford", "Cheadle", "Hale", "Wilmslow",
  ];

  const handleNext = async () => {
    if (!selectedOption) return;

    // ✅ Step 1: Update answers and show loading screen
    const updatedAnswers = { ...answers, Location: selectedOption };

    try {
      // ✅ Step 2: Send to server
      //http://localhost:4000/api/estimate
      const res = await fetch("http://13.60.223.46:4000/api/estimate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedAnswers),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Prediction failed");

      // ✅ Step 3: Pass both updated answers + cost to parent
      onNext({
        cost: data.predicted_cost
      });
    } catch (err) {
      console.error("Error fetching estimate:", err);
      onNext({
        ...updatedAnswers,
        cost: 0,
      });
    } finally {
      
    }
  };



  // ✅ Step 5: Normal form UI
  return (
    <MotionBox
      key="location"
      initial={{ opacity: 0, y: 80 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -80 }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      p={8}
      bg="white"
      rounded="2xl"
      shadow="xl"
      textAlign="center"
      maxW="700px"
      color="gray.800"
    >
      <Heading mb={8}>Where is your property?</Heading>

      <Box
        as="select"
        size="lg"
        rounded="full"
        bg="white"
        borderWidth="2px"
        borderColor="gray.300"
        focusBorderColor="teal.500"
        mb={8}
        px={4}
        py={3}
        width="100%"
        value={selectedOption}
        onChange={(e) => setSelectedOption(e.target.value)}
      >
        <option value="">Select a location</option>
        {options
          .slice()
          .sort((a, b) => a.localeCompare(b))
          .map((option, index) => (
            <option key={index} value={option}>
              {option}
            </option>
          ))}
      </Box>

      <Box mt={6}>
        <Button
          colorScheme="gray"
          rounded="full"
          onClick={onBack}
          mr={4}
          variant="ghost"
        >
          Back
        </Button>
        <Button
          colorScheme="teal"
          rounded="full"
          onClick={handleNext}
          isDisabled={!selectedOption}
        >
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
