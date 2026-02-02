import { Box, Button, Heading, VStack, Input, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function SqftToReno({ onBack, onNext, answers }) {
  const renovationTypes = answers?.renovation_type ?? [];
  const bedroomCount = answers?.bedrooms_to_reno ?? 0;
  const bathroomCount = answers?.bathrooms_to_reno ?? 0;
  const isFullReno = renovationTypes.includes("Full renovation");


  // Build dynamic input structure just like SqftToAdd
  const initialValues = isFullReno
  ? {
      bedrooms: [],
      bathrooms: [],
      other: { "Full renovation": "" }
    }
  : {
      bedrooms: Array(bedroomCount).fill(""),
      bathrooms: Array(bathroomCount).fill(""),
      other: renovationTypes
        .filter(r => !["Bedroom", "Bathroom"].includes(r))
        .reduce((acc, cur) => ({ ...acc, [cur]: "" }), {})
    };


  const [values, setValues] = useState(initialValues);

  const handleUpdate = (group, indexOrKey, val) => {
  if (!/^\d*$/.test(val)) return;

  // ✅ Full renovation owns this screen
  if (group === "other" && indexOrKey === "Full renovation") {
    setValues(prev => ({
      ...prev,
      other: { "Full renovation": val }
    }));
    return;
  }

  // 🚫 Block all other updates if full renovation exists
  if (values.other?.["Full renovation"] !== undefined) {
    return;
  }

  if (group === "other") {
    setValues(prev => ({
      ...prev,
      other: { ...prev.other, [indexOrKey]: val }
    }));
  } else {
    const copy = [...values[group]];
    copy[indexOrKey] = val;
    setValues(prev => ({ ...prev, [group]: copy }));
  }
};


  const allFilled =
  values.other?.["Full renovation"] !== undefined
    ? values.other["Full renovation"] !== ""
    : values.bedrooms.every(v => v !== "") &&
      values.bathrooms.every(v => v !== "") &&
      Object.values(values.other).every(v => v !== "");

  const handleNext = () => {
    onNext({
      sqft_renovated: {
        bedrooms: values.bedrooms.map(Number),
        bathrooms: values.bathrooms.map(Number),
        other: Object.fromEntries(
          Object.entries(values.other).map(([k, v]) => [k, Number(v)])
        )
      }
    });

  };

  return (
    <MotionBox
      key="sqft-reno"
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
      <Heading mb={8}>Sqft to Renovate</Heading>

      {/* 🔥 Scrollable input list same as SqftToAdd */}
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
            <Text fontWeight="medium" fontSize="md" mb={1}>Bedroom {i + 1}</Text>
            <Input
              placeholder="Enter sqft to renovate"
              rounded="full"
              textAlign="center"
              value={v}
              onChange={(e) => handleUpdate("bedrooms", i, e.target.value)}
              _hover={{ borderColor: "teal.500" }}
              _focus={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              _focusVisible={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              transition="all .2s"
            />
          </Box>
        ))}

        {/* Bathrooms */}
        {!isFullReno && values.bathrooms.map((v, i) => (
          <Box key={`bath-${i}`} p={6} rounded="2xl" border="1px solid" borderColor="gray.300" shadow="md" w="100%" textAlign="left">
            <Text fontWeight="medium" fontSize="md" mb={1}>Bathroom {i + 1}</Text>
            <Input
              placeholder="Enter sqft to renovate"
              rounded="full"
              textAlign="center"
              value={v}
              onChange={(e) => handleUpdate("bathrooms", i, e.target.value)}
              _hover={{ borderColor: "teal.500" }}
              _focus={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              _focusVisible={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              transition="all .2s"
            />
          </Box>
        ))}

        {/* Other rooms selected */}
        {Object.keys(values.other)
          .filter(room =>
            room === "Full renovation" ||
            !values.other["Full renovation"]
          )
          .map((room) => (

          <Box key={room} p={6} rounded="2xl" border="1px solid" borderColor="gray.300" shadow="md" w="100%" textAlign="left">
            <Text fontWeight="medium" fontSize="md" mb={1}>{room}</Text>
            <Input
              placeholder="Enter sqft to renovate"
              rounded="full"
              textAlign="center"
              value={values.other[room]}
              onChange={(e) => handleUpdate("other", room, e.target.value)}
              _hover={{ borderColor: "teal.500" }}
              _focus={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              _focusVisible={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              transition="all .2s"
            />
          </Box>
        ))}
      </VStack>

      <Box mt={10}>
        <Button variant="ghost" colorScheme="gray" rounded="full" mr={4} onClick={onBack}>
          Back
        </Button>
        <Button
          rounded="full"
          px={8}
          bg={allFilled ? "black" : "gray.600"}
          color="white"
          opacity={allFilled ? 1 : 0.6}
          cursor={allFilled ? "pointer" : "not-allowed"}
          isDisabled={!allFilled}
          onClick={allFilled ? handleNext : undefined}
        >
          Next
        </Button>
      </Box>

    </MotionBox>
  );
}
