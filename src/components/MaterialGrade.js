import { Box, Button, Heading, VStack, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function MaterialGrade({ onBack, onNext, answers }) {
  const renovationTypes = answers?.renovation_type || [];

  const [selectedMaterials, setSelectedMaterials] = useState(
    Array(renovationTypes.length).fill("")
  );

  const options = ["High-end", "Mid-range", "Budget-friendly"];

  const handleChange = (index, value) => {
    const updated = [...selectedMaterials];
    updated[index] = value;
    setSelectedMaterials(updated);
  };

  const allSelected = selectedMaterials.every((m) => m !== "");

  return (
    <MotionBox
      key="material-grade"
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
    >
      <Heading mb={8}>Select material grade for each renovation area</Heading>

      <VStack spacing={6} w="100%">
        {renovationTypes.map((type, index) => (
          <Box
            key={index}
            p={6}
            rounded="2xl"
            border="1px solid"
            borderColor="gray.300"
            shadow="md"
            w="100%"
            textAlign="left"
          >
            <Text fontWeight="bold" mb={3}>{type}</Text>

            <Box
              as="select"
              size="lg"
              rounded="full"
              bg="white"
              borderWidth="2px"
              borderColor="teal.500"
              px={4}
              py={2}
              w="100%"
              value={selectedMaterials[index]}
              onChange={(e) => handleChange(index, e.target.value)}
              sx={{
                appearance: "none",
              }}
              _focus={{
                borderColor: "teal.500",
                boxShadow: "0 0 0 2px rgba(56, 178, 172, 0.6) !important", // teal shadow
                outline: "none",
              }}
              _focusVisible={{
                borderColor: "teal.500",
                outline: "none",
                boxShadow: "none !important",
              }}
              _hover={{ borderColor: "teal.500" }}
            >

              <option value="">Choose material grade</option>
              {options.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </Box>
          </Box>
        ))}
      </VStack>

      <Box mt={8}>
        <Button
          colorScheme="gray"
          rounded="full"
          mr={4}
          variant="ghost"
          onClick={onBack}
        >
          Back
        </Button>

        <Button
          bg={allSelected ? "black" : "gray.600"}
          color="white"
          rounded="full"
          px={8}
          opacity={allSelected ? 1 : 0.6}
          cursor={allSelected ? "pointer" : "not-allowed"}
          isDisabled={!allSelected}
          onClick={() => allSelected && onNext({ material_grades: selectedMaterials })}
        >
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
