import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePage } from "@/contexts/PageContext";
import { House } from "lucide-react";

type Props = {};

const CreateImage = (props: Props) => {
  const { setCurrentPage } = usePage();
  const [instructions, setInstructions] = useState("");
  const [referenceImage, setReferenceImage] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [openPopover, setOpenPopover] = useState(false);

  const placeholderImages = [
    "/placeholder.png",
    "/placeholder2.png",
    "/placeholder3.png",
  ];

  const handleSelectImage = (img: string) => {
    setReferenceImage(img);
    setOpenPopover(false);
  };

  const handleGenerate = () => {
    // In real case: call image generation API here
    // For now, just mock it
    setGeneratedImage("/generated_sample.png");
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage("home")}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3">Create Image</div>
      </div>

      {/* Generated Image Preview */}
        <div className="w-full flex justify-center mt-5">
          <img
            src={generatedImage? "": ""}
            alt="Generated"
            className="max-w-[80%] max-h-[400px] object-contain border border-gray-300 rounded-md"
          />
        </div>

      {/* Instructions */}
      <div className="px-5 mb-5 mt-6">
        <Label className="mb-1">Enter Instructions</Label>
        <Textarea
          className="text-sm mt-2"
          placeholder="Describe what you want to generate..."
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
        />
      </div>

      {/* Image Reference Input */}
      <div className="px-5 mb-5">
        <Label className="mb-1">Insert Image for Reference</Label>
        <Popover open={openPopover} onOpenChange={setOpenPopover}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="mt-2">
              {referenceImage ? "Change Image" : "Add Image"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-96 p-4">
            <Card>
              <CardHeader>
                <CardTitle>Select or Upload Image</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <Button
                  variant="outline"
                  onClick={() => alert("Import from device (placeholder)")}
                >
                  Import from device
                </Button>

                <div className="grid grid-cols-3 gap-2">
                  {placeholderImages.map((img) => (
                    <img
                      key={img}
                      src={img}
                      alt="placeholder"
                      className={`w-full h-24 object-cover border rounded-md cursor-pointer ${
                        referenceImage === img ? "ring-2 ring-blue-500" : ""
                      }`}
                      onClick={() => handleSelectImage(img)}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          </PopoverContent>
        </Popover>

        {referenceImage && (
          <div className="mt-3">
            <img
              src={referenceImage}
              alt="Reference"
              className="w-48 h-32 object-cover border border-gray-300 rounded-md"
            />
          </div>
        )}
      </div>

      {/* Generate Button */}
      <div className="px-5 mb-10">
        <Button className="w-full" onClick={handleGenerate}>
          Generate
        </Button>
      </div>
    </div>
  );
};

export default CreateImage;
