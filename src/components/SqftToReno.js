import { Box, Button, Heading, Input, Field, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function SqftToReno({ onBack, onNext }) {
  const [sqft, setSqft] = useState("");
  const [showError, setShowError] = useState(false);

  // ✅ Validation checks
  const isEmpty = sqft.trim().length === 0;
  const isZeroOrNegative = !isEmpty && Number(sqft) <= 0;
  const canProceed = !isEmpty && !isZeroOrNegative;

  const handleNext = () => {
    if (!canProceed) {
      setShowError(true);
      return;
    }
    setShowError(false);
    onNext({sqft_renovated : parseInt(sqft)});
  };

  const handleInputChange = (e) => {
    const value = e.target.value;

    // ✅ Allow only digits
    if (/^\d*$/.test(value)) {
      setSqft(value);
      if (showError) setShowError(false);
    }
  };

  // ✅ Choose the right error message
  let errorMessage = "";
  if (showError) {
    if (isEmpty) errorMessage = "Please enter a value.";
    else if (isZeroOrNegative) errorMessage = "Please enter a number greater than 0.";
  }

  return (
    <MotionBox
      key="question6"
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
      <Heading mb={6}>Number of sqft to be renovated?</Heading>

      {/* ✅ Input */}
      <Field.Root invalid={showError && !canProceed}>
        <Input
          type="text"
          placeholder="Enter the sqft to be renovated"
          size="lg"
          rounded="full"
          textAlign="center"
          fontSize="sm"
          value={sqft}
          onChange={handleInputChange}
          focusBorderColor="teal.500"
        />
      </Field.Root>

      {/* ✅ Dynamic Error Message */}
      {showError && errorMessage && (
        <Box display="flex" justifyContent="center">
          <Text
            mt={2}
            fontSize="sm"
            color="red.500"
            width="fit-content"
            textAlign="center"
          >
            {errorMessage}
          </Text>
        </Box>
      )}

      {/* ✅ Buttons */}
      <Box mt={8}>
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
          bg={canProceed ? "black" : "gray.600"}
          color="white"
          opacity={canProceed ? 1 : 0.6}
          cursor={canProceed ? "pointer" : "not-allowed"}
          isDisabled={!canProceed}
        onClick={handleNext}>
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
