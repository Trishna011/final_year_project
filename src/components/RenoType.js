import { Box, Button, Heading, SimpleGrid } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function RenoType({ onBack, onNext, step }) {
  const [selectedOptions, setSelectedOptions] = useState([]);

  const options = [
    { id: 1, label: "Full renovation" },
    { id: 2, label: "Bedroom" },
    { id: 3, label: "Kitchen" },
    { id: 4, label: "Bathroom" },
    { id: 5, label: "Living room" },
    { id: 6, label: "Other/Custom" },
  ];

  const toggleOption = (label) => {
    setSelectedOptions((prev) =>
      prev.includes(label)
        ? prev.filter((item) => item !== label) // remove if already selected
        : [...prev, label] // add if not selected
    );
  };

  return (
    <Box
      p={8}
      bg="white"
      rounded="2xl"
      shadow="xl"
      textAlign="center"
      maxW="700px"
      color="gray.800"
    >
      <Heading mb={8} textAlign="center">
        What would you like to renovate?
      </Heading>
      <SimpleGrid columns={{ base: 1, sm: 2 }} spacing={8}>
        {options.map((option) => {
          const isSelected = selectedOptions.includes(option.label);
          
          return (
          <MotionBox
            key={option.id}
            p={8}
            rounded="xl"
            borderWidth="2px"
            borderColor={isSelected ? "teal.500" : "gray.200"}
            bg={isSelected ? "teal.50" : "white"}
            color="gray.700"
            textAlign="center"
            fontWeight="semibold"
            cursor="pointer"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => toggleOption(option.label)}
              transition={{ duration: 0.2 }}
            >
            {option.label}
          </MotionBox>
          );
        })}
      </SimpleGrid>

      <Box mt={10}>
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
          bg={selectedOptions.length === 0 ? "gray.600" : "black"}
          color="white"
          rounded="full"
          px={8}
          opacity={selectedOptions.length === 0 ? 0.6 : 1}
          cursor={selectedOptions.length === 0 ? "not-allowed" : "pointer"}
          isDisabled={selectedOptions.length === 0}
          onClick={() => selectedOptions.length > 0 && onNext({ renovation_type: selectedOptions })}
        >
          Next
        </Button>
      </Box>

    </Box>
  );
}
