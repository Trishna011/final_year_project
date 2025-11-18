import { Box, Button, Heading, SimpleGrid } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function RenoType({ onBack, onNext, step }) {
  const [selectedOption, setSelectedOption] = useState(null);

  const options = [
    { id: 1, label: "Full renovation" },
    { id: 2, label: "Bedroom" },
    { id: 3, label: "Kitchen" },
    { id: 4, label: "Bathroom" },
    { id: 5, label: "Living room" },
    { id: 6, label: "Other/Custom" },
  ];

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
        {options.map((option) => (
          <MotionBox
            key={option.id}
            p={8}
            rounded="xl"
            borderWidth="2px"
            borderColor={
              selectedOption === option.label ? "teal.500" : "gray.200"
            }
            bg={selectedOption === option.label ? "teal.50" : "white"}
            color="gray.700"
            textAlign="center"
            fontWeight="semibold"
            cursor="pointer"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => setSelectedOption(option.label)} // ✅ store label
            transition={{ duration: 0.2 }}
          >
            {option.label}
          </MotionBox>
        ))}
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
          colorScheme="teal"
          rounded="full"
          isDisabled={!selectedOption}
          onClick={() => {
            if (selectedOption) onNext({renovation_type: selectedOption }); // ✅ send label text to App.js
          }}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}
