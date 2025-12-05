import { Box, Button, Heading, Input, Field, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function SqftToAdd({ onBack, onNext }) {
  const [addSqft, setAddSqft] = useState("");

  const canProceed = addSqft.trim().length > 0;

  const handleNext = () => {
    onNext({sqft_to_add_to_property : parseInt(addSqft)});
  };

  const handleInputChange = (e) => {
    const value = e.target.value;

    // 👇 Allow only digits (no letters, symbols, or spaces)
    if (/^\d*$/.test(value)) {
      setAddSqft(value);
    }
  };

  return (
    <MotionBox
      key="question7"
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
      <Heading mb={6}>Are you doing an extension?</Heading>

      {/* ✅ Input */}
      <Field.Root>
        <Input
          placeholder="Enter sqft to add - 0 if none"
          size="lg"
          rounded="full"
          textAlign="center"
          fontSize="sm"
          value={addSqft}
          onChange={handleInputChange}
          focusBorderColor="teal.500"
        />
      </Field.Root>

      {/* 🚀 Navigation */}
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
          onClick={() => canProceed && onNext({ sqft_to_add_to_property: parseInt(addSqft) })}
        >
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
