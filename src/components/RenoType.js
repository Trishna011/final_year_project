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
  setSelectedOptions((prev) => {
    let updated;

    // Toggle clicked item
    if (prev.includes(label)) {
      updated = prev.filter((item) => item !== label);
    } else {
      updated = [...prev, label];
    }

    // Selecting FULL RENOVATION removes others immediately
    if (label === "Full renovation") return ["Full renovation"];

    // If Full renovation was selected before & another option is selected → remove it
    if (updated.includes("Full renovation") && label !== "Full renovation") {
      updated = updated.filter((item) => item !== "Full renovation");
    }

    // --- ✨ If user selects 4 other options → delay change to full renovation ✨ ---
    const nonFullCount = updated.filter((item) => item !== "Full renovation").length;

    if (nonFullCount === 4) {
      // Temporarily show all 4 options before switching
      setTimeout(() => {
        setSelectedOptions(["Full renovation"]); // Switch after delay
      }, 350); // 👈 Adjust speed here (700ms feels nice)

      return updated; // Shows the 4 options briefly
    }

    return updated;
  });
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
              transition={{ duration: 0.2 }}
              onClick={() => toggleOption(option.label)}
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
          onClick={() =>
            selectedOptions.length > 0 &&
            onNext({ renovation_type: selectedOptions })
          }
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}
