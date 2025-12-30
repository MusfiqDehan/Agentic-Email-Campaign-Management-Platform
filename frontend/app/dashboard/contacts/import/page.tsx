"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle2 } from "lucide-react";
import api from "@/config/axios";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/components/ui/use-toast";

const importSchema = z.object({
  list_id: z.string().optional(),
  file: z.any().refine((files) => files?.length > 0, "File is required"),
  update_existing: z.boolean().default(false),
  tags: z.string().optional(),
});

type ImportFormValues = z.infer<typeof importSchema>;

interface ContactList {
  id: string;
  name: string;
}

export default function ImportContactsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [lists, setLists] = useState<ContactList[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  const form = useForm({
    resolver: zodResolver(importSchema),
    defaultValues: {
      update_existing: false,
      tags: "",
    },
  });

  useEffect(() => {
    const fetchLists = async () => {
      try {
        const response = await api.get("/campaigns/contact-lists/");
        setLists(response.data.results || response.data);
      } catch (error) {
        console.error("Failed to fetch contact lists", error);
        toast({
          title: "Error",
          description: "Failed to load contact lists",
          variant: "destructive",
        });
      }
    };

    fetchLists();
  }, [toast]);

  const onSubmit = async (data: ImportFormValues) => {
    setIsLoading(true);
    setImportResult(null);

    try {
      const formData = new FormData();

      if (data.list_id && data.list_id !== "none") {
        formData.append("list_id", data.list_id);
      }

      formData.append("file", data.file[0]);
      formData.append("update_existing", data.update_existing.toString());

      if (data.tags) {
        // Split tags by comma and append each
        const tagsList = data.tags.split(",").map(t => t.trim()).filter(t => t);
        tagsList.forEach(tag => formData.append("tags", tag));
      }

      const response = await api.post("/campaigns/contacts/bulk/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setImportResult(response.data);
      toast({
        title: "Import Successful",
        description: `Processed ${response.data.total || response.data.total_processed || 0} contacts.`,
      });

      // Reset file input
      form.reset({ ...data, file: undefined as any });

    } catch (error: any) {
      console.error("Import failed", error);
      toast({
        title: "Import Failed",
        description: error.response?.data?.detail || "An error occurred during import.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-10 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Import Contacts</h1>
        <p className="text-muted-foreground">
          Upload a CSV or Excel file to bulk import contacts.
        </p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Upload File</CardTitle>
            <CardDescription>
              Your file must contain an "email" column. Optional columns: first_name, last_name, phone.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">

                <FormField
                  control={form.control}
                  name="list_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Add to List (Optional)</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a contact list" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="none">Do not add to any list</SelectItem>
                          {lists.map((list) => (
                            <SelectItem key={list.id} value={list.id}>
                              {list.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Select a list to automatically add imported contacts to.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="file"
                  render={({ field: { onChange, value, ...field } }) => (
                    <FormItem>
                      <FormLabel>CSV or Excel File</FormLabel>
                      <FormControl>
                        <div className="flex items-center justify-center w-full">
                          <label
                            htmlFor="dropzone-file"
                            className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 dark:hover:bg-gray-800 dark:bg-gray-900 border-gray-300 dark:border-gray-700"
                          >
                            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                              <Upload className="w-8 h-8 mb-3 text-gray-400" />
                              <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                                <span className="font-semibold">Click to upload</span> or drag and drop
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                CSV, XLSX (MAX. 10MB)
                              </p>
                            </div>
                            <Input
                              id="dropzone-file"
                              type="file"
                              accept=".csv, .xlsx, .xls"
                              className="hidden"
                              onChange={(e) => {
                                onChange(e.target.files);
                              }}
                              {...field}
                            />
                          </label>
                        </div>
                      </FormControl>
                      {value && value.length > 0 && (
                        <div className="flex items-center gap-2 mt-2 text-sm text-green-600">
                          <FileSpreadsheet className="h-4 w-4" />
                          {value[0].name}
                        </div>
                      )}
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="tags"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tags (Optional)</FormLabel>
                      <FormControl>
                        <Input placeholder="imported, 2024-leads" {...field} />
                      </FormControl>
                      <FormDescription>
                        Comma-separated tags to apply to all imported contacts.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="update_existing"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                      <div className="space-y-1 leading-none">
                        <FormLabel>
                          Update existing contacts
                        </FormLabel>
                        <FormDescription>
                          If checked, existing contacts with the same email will be updated with new data.
                        </FormDescription>
                      </div>
                    </FormItem>
                  )}
                />

                <div className="flex justify-end gap-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.back()}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isLoading}>
                    {isLoading ? "Importing..." : "Start Import"}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>

        {importResult && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                Import Results
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-md text-center">
                  <div className="text-2xl font-bold">{importResult.total || 0}</div>
                  <div className="text-xs text-muted-foreground uppercase">Processed</div>
                </div>
                <div className="bg-green-100 dark:bg-green-900/30 p-3 rounded-md text-center">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">{importResult.created || 0}</div>
                  <div className="text-xs text-muted-foreground uppercase">Created</div>
                </div>
                <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-md text-center">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{importResult.updated || 0}</div>
                  <div className="text-xs text-muted-foreground uppercase">Updated</div>
                </div>
                <div className="bg-yellow-100 dark:bg-yellow-900/30 p-3 rounded-md text-center">
                  <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{importResult.skipped || 0}</div>
                  <div className="text-xs text-muted-foreground uppercase">Skipped</div>
                </div>
                <div className="bg-red-100 dark:bg-red-900/30 p-3 rounded-md text-center">
                  <div className="text-2xl font-bold text-red-600 dark:text-red-400">{importResult.errors?.length || 0}</div>
                  <div className="text-xs text-muted-foreground uppercase">Errors</div>
                </div>
              </div>

              {importResult.errors && importResult.errors.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-red-500" />
                    Error Details
                  </h4>
                  <div className="bg-slate-50 dark:bg-slate-900 p-4 rounded-md max-h-60 overflow-y-auto text-sm">
                    <ul className="space-y-1">
                      {importResult.errors.map((err: any, idx: number) => (
                        <li key={idx} className="text-red-600 dark:text-red-400">
                          Row {err.row}: {err.error} ({err.email})
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
