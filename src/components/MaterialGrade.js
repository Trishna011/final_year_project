import { Box, Button, Heading, SimpleGrid } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function MaterialGrade({ onBack, onNext }) {
  const [selectedOption, setSelectedOption] = useState(null);


  const options = [
    { id: 1, label: "High-end" },
    { id: 2, label: "Mid-range" },
    { id: 3, label: "Budget-friendly" }
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
        What type of material would you like to use?
      </Heading>

      <SimpleGrid columns={1} spacing={4}>
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
            onClick={() => setSelectedOption(option.label)}
            transition={{ duration: 0.2 }}
          >
            {option.label}
          </MotionBox>
        ))}
      </SimpleGrid>

      <Box mt={10}>
        <Button
          colorScheme="grey"
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
            if (selectedOption) onNext({material_grade : selectedOption }); // ✅ trigger next step in App.js
          }}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}
