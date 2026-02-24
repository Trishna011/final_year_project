import { Box, Button, Heading, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function Location({ onBack, onNext, answers }) {
  const [selectedOption, setSelectedOption] = useState("");
  const [showError, setShowError] = useState(false);

  const options = [
    "Manchester City Centre", "Salford", "Stockport", "Bolton", "Bury", "Oldham",
    "Rochdale", "Tameside", "Trafford", "Wigan", "Altrincham",
    "Ashton-under-Lyne", "Prestwich", "Didsbury", "Chorlton", "Withington",
    "Levenshulme", "Sale", "Stretford", "Cheadle", "Hale", "Wilmslow",
  ];

  const handleNext = async () => {
    if (!selectedOption) {
      setShowError(true);
      return;
    }
    setShowError(false);

    // ✅ Step 1: Update answers and show loading screen
    const updatedAnswers = { ...answers, Location: selectedOption };

    try {
      // ✅ Step 2: Send to server
      //http://13.60.223.46:4000/api/estimate
      const res = await fetch("http://localhost:4000/api/estimate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedAnswers),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Prediction failed");

      const renovationCost = data.total_predicted_cost;

      //send all inputs and cost to server to find projected val of property post renovation
      const valueRes = await fetch("http://localhost:4000/api/value", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...updatedAnswers,
          renovation_cost: renovationCost,
        }),
      });

      const valueData = await valueRes.json();
      if (!valueRes.ok) throw new Error("Value prediction failed");
      // ✅ Step 3: Pass both updated answers + cost to parent
      onNext({
        ...updatedAnswers,
        cost: data.total_predicted_cost,
        postRenovationValue: valueData.post_renovation_value,
      });
    } catch (err) {
      onNext({
        ...updatedAnswers,
        cost: 0,
        postRenovationValue: 0,
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
        borderWidth="1px"
        borderColor="teal.500"
        px={4}
        py={3}
        width="100%"
        mb={8}
        value={selectedOption}
        onChange={(e) => {
          const value = e.target.value
          setSelectedOption(value)

          if (value) {
          setShowError(false)
          }
        }}
        sx={{
          appearance: "none",
          outline: "none",
        }}
        _focus={{
          borderColor: "teal.500 !important",
          boxShadow: "0 0 0 2px rgba(56, 178, 172, 0.6) !important", // subtle teal glow
          outline: "none"
        }}
        _focusVisible={{
          borderColor: "teal.500 !important",
          boxShadow: "none !important",
          outline: "none",
        }}
        _hover={{ borderColor: "teal.500" }}
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

      {showError && (
                    <Box display="flex" justifyContent="center">
                      <Text
                        mt={2}
                        fontSize="sm"
                        color="red.500"
                        width="fit-content"
                        textAlign="center"
                      >
                        Please answer all rooms before continuing
                      </Text>
                    </Box>
                  )}


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
          rounded="full"
          px={8}
          bg="black"
          color="white"
          onClick={handleNext}
        >
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
