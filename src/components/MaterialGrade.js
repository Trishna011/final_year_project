import { Box, Button, Heading, VStack, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function MaterialGrade({ onBack, onNext, answers }) {
  const renovationTypes = answers?.renovation_type ?? [];
  const bedroomCount = answers?.bedrooms_to_reno ?? 0;
  const bathroomCount = answers?.bathrooms_to_reno ?? 0;
  const isFullReno = renovationTypes.includes("Full renovation");


  const otherTypes = renovationTypes.filter(
    r => !["Bedroom", "Bathroom"].includes(r)
  );

  // Initialize dynamic selections
  const initialValues = isFullReno
  ? {
      bedrooms: [],
      bathrooms: [],
      other: { "Full renovation": "" }
    }
  : {
      bedrooms: Array(bedroomCount).fill(""),
      bathrooms: Array(bathroomCount).fill(""),
      other: otherTypes.reduce((acc, cur) => ({ ...acc, [cur]: "" }), {})
    };


  const [values, setValues] = useState(initialValues);
  const [showError, setShowError] = useState(false);

  const materialOptions = ["High-end", "Mid-range", "Budget-friendly"];

  const updateSelection = (group, indexOrKey, value) => {
    // Full renovation owns the screen
    if (group === "other" && indexOrKey === "Full renovation") {
      setValues(prev => ({
        ...prev,
        other: { "Full renovation": value }
      }));
      return;
    }

    // Block all other updates if full renovation exists
    if (values.other?.["Full renovation"] !== undefined) {
      return;
    }

    if (group === "other") {
      setValues(prev => ({
        ...prev,
        other: { ...prev.other, [indexOrKey]: value }
      }));
    } else {
      const updated = [...values[group]];
      updated[indexOrKey] = value;
      setValues(prev => ({ ...prev, [group]: updated }));
    }
  };


  const allSelected =
  values.other?.["Full renovation"] !== undefined
    ? values.other["Full renovation"] !== ""
    : values.bedrooms.every(v => v !== "") &&
      values.bathrooms.every(v => v !== "") &&
      Object.values(values.other).every(v => v !== "");


  const handleNext = () => {
    if (!allSelected) {
      setShowError(true);
      return;
    }
    setShowError(false);
    onNext({
      material_grade: {
        bedrooms: values.bedrooms,
        bathrooms: values.bathrooms,
        other: values.other
      }
    });
  };

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
      maxW="700px"
      textAlign="center"
      color="gray.800"
    >
      <Heading mb={8}>Select Material Grade</Heading>

      {/* Scrollable container like your Sqft pages */}
      <VStack
        spacing={6}
        w="100%"
        maxH="400px"
        overflowY="auto"
        pr={2}
        sx={{
          "&::-webkit-scrollbar": { width: "6px" },
          "&::-webkit-scrollbar-thumb": { background: "#d1d1d1", borderRadius: "10px" }
        }}
      >

        {/* Bedrooms */}
        {!isFullReno && values.bedrooms.map((v, i) => (
          <Box key={`bed-${i}`} p={6} rounded="2xl" border="1px solid" borderColor="gray.300" shadow="md" w="100%" textAlign="left">
            <Text fontWeight="medium" mb={2}>Bedroom {i + 1} Material</Text>

            <Box
              as="select"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
              w="100%"
              size="lg"
              px={2.5}
              py={1.5}
              value={v}
              onChange={(e) => updateSelection("bedrooms", i, e.target.value)}
              _hover={{ borderColor: "teal.500" }}
              _focus={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              _focusVisible={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
            >
              <option value="">Choose material grade</option>
              {materialOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </Box>
          </Box>
        ))}

        {/* Bathrooms */}
        {!isFullReno && values.bathrooms.map((v, i) => (
          <Box key={`bath-${i}`} p={6} rounded="2xl" border="1px solid" borderColor="gray.300" shadow="md" w="100%" textAlign="left">
            <Text fontWeight="medium" mb={2}>Bathroom {i + 1} Material</Text>

            <Box
              as="select"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
              w="100%"
              size="lg"
              px={2.5}
              py={1.5}
              value={v}
              onChange={(e) => updateSelection("bathrooms", i, e.target.value)}
              _hover={{ borderColor: "teal.500" }}
              _focus={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              _focusVisible={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
            >
              <option value="">Choose material grade</option>
              {materialOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </Box>
          </Box>
        ))}

        {/* Other renovation types */}
        {Object.keys(values.other)
          .filter(room =>
            room === "Full renovation" ||
            !values.other["Full renovation"]
          )
          .map(room => (
          <Box key={room} p={6} rounded="2xl" border="1px solid" borderColor="gray.300" shadow="md" w="100%" textAlign="left">
            <Text fontWeight="medium" mb={2}>{room} Material</Text>

            <Box
              as="select"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
              w="100%"
              size="lg"
              px={2.5}
              py={1.5}
              value={values.other[room]}
              onChange={(e) => updateSelection("other", room, e.target.value)}
              _hover={{ borderColor: "teal.500" }}
              _focus={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              _focusVisible={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
            >
              <option value="">Choose material grade</option>
              {materialOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </Box>
          </Box>
        ))}

      </VStack>

      {showError && (
        <Box display="flex" justifyContent="center">
          <Text
            mt={2}
            fontSize="sm"
            color="red.500"
            width="fit-content"
            textAlign="center"
          >
            Please select a material grade for all rooms
          </Text>
        </Box>
      )}

      <Box mt={10}>
        <Button variant="ghost" colorScheme="gray" rounded="full" mr={4} onClick={onBack}>
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
