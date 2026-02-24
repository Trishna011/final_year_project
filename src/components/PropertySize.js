import { Box, Button, Heading, Input, Field, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function PropertySize({ onBack, onNext }) {
  const [size, setSize] = useState("");
  const [showError, setShowError] = useState(false);

  const isEmpty = size.trim().length === 0;
  const isZeroOrNegative = !isEmpty && Number(size) <= 0;
  const canProceed = !isEmpty && !isZeroOrNegative;

  const handleNext = () => {
    if (!canProceed) {
      setShowError(true);
      
      return;
    }
    setShowError(false);
    onNext({property_size : parseInt(size)});
  };

  const handleInputChange = (e) => {
    const value = e.target.value;

    // ✅ Allow only digits
    if (/^\d*$/.test(value)) {
      setSize(value);
      if (showError) setShowError(false);
    }
  };

  // ✅ Choose the right error message
  let errorMessage = "";
  if (showError) {
    if (isEmpty) errorMessage = "Please enter a value";
    else if (isZeroOrNegative) errorMessage = "Please enter a number greater than 0";
  }

  return (
    <MotionBox
      key="question2"
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
      <Heading mb={6}>What is the property size?</Heading>

      {/* ✅ Input */}
      <Field.Root invalid={showError && !canProceed}>
        <Input
          placeholder="Enter the property size in sqft"
          size="lg"
          rounded="full"
          textAlign="center"
          fontSize="sm"
          value={size}
          onChange={handleInputChange}

          borderColor="gray.300"
          _hover={{ borderColor: "teal.500" }}

          // 🔥 makes hover & focus identical
          _focus={{
            borderColor: "teal.500",
            boxShadow: "none",      // removes thick halo/glow
            outline: "none"         // removes browser highlighting fallback
          }}

          _focusVisible={{
            borderColor: "teal.500",
            boxShadow: "none",
            outline: "none"
          }}

          transition="all .2s"
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

      {/* ✅ Navigation buttons */}
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
          bg={"black"}
          color="white"
          onClick={handleNext}>
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
