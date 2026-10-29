import gradio as gr
from dotenv import load_dotenv

from answer import answer_question

load_dotenv(override=True)


def format_context(context):
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"
    for doc in context:
        result += f"<span style='color: #ff7800;'>Source: {doc.metadata['source']}</span>\n\n"
        result += doc.page_content + "\n\n"
    return result


def chat(history): #you'll see below that the whole chatbot(including newest msg) is passed in as history
    last_message = history[-1]["content"]
    prior = history[:-1]
    #remember: answer_question returns both llm answer AND contexts fetched from vector store
    answer, context = answer_question(last_message, prior)
    history.append({"role": "assistant", "content": answer}) #add to the history
    return history, format_context(context)


def main():
    #this simply adds the new message to the history window and clears the message box
    #it's cosmetically updating the chatbot
    def put_message_in_chatbot(message, history):
        return "", history + [{"role": "user", "content": message}]

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Content Hub Asset Assistant", theme=theme) as ui:
        gr.Markdown("# 🏢 Content Hub Assistant\nAsk me anything about Content Hub assets!")

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="💬 Conversation", height=600, type="messages", show_copy_button=True
                )
                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about Content Hub assets...",
                    show_label=False,
                )

            with gr.Column(scale=1):
                context_markdown = gr.Markdown(
                    label="📚 Retrieved Context",
                    value="*Retrieved context will appear here*",
                    container=True,
                    height=600,
                )

        message.submit(
            put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]
        ).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()