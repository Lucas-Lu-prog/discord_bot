import os
import random
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(dotenv_path="config")


class MyClient(commands.Bot):
    
    def __init__(self):
        super().__init__(command_prefix=">>")
        self.client = discord.Client()
        self.add_commands()

    @staticmethod
    async def on_ready():
        print("Le bot est prêt")

    @staticmethod
    async def get_bank_info():

        """
            Permet des donnes contenues dans le fichier JSON.
        """

        # Ouverture du fichier JSON en lecture
        with open("main_bank.json", "r") as f:
            users = json.load(f)
        f.close()

        return users

    @staticmethod
    async def does_user_has_account(user_id, users):

        """
            Cette fonction permet la verification de l'existence ou non d'un compte.
            Renvoie un BOOLEAN
        """

        # On verifie qu'il n'y ait aucun compte a l'ID donnee
        if str(user_id) in users:
            return True
        else:
            return False

    @staticmethod
    async def does_amount_equals_zero(user_id, users):

        """
            Permet de verifier qu'un compte ne soit pas a 0$.
            Renvoie un BOOLEAN
        """

        # On verifie si le montant du compte n'est pas egal a zero
        if users[str(user_id)]["safe_deposit_box"] == 0:
            return True
        else:
            return False

    @staticmethod
    async def save_bank_info(users):

        """
            Permet l'ecriture des donnees finales dans le Fichier JSON
        """

        # Ouverture du fichier JSON en mode ecriture
        with open("main_bank.json", "w") as f:
            json.dump(users, f, indent=4)

        f.close()

    async def open_account(self, user):

        """
            Permet l'ouveture d'un compte et la sauvegarde du compte sur le Fichier JSON
            dans le cas ou l'utilisateur n'en possede pas.
            Renvoie un BOOLEAN
        """

        users = await self.get_bank_info()

        user_id = user.id

        # Condition de BOOLEAN : si la fonction retourne TRUE alors pass ( compte existant ) sinon creation du compte
        if await self.does_user_has_account(user_id, users):
            pass
        else:
            users[str(user_id)] = {}
            users[str(user_id)]["safe_deposit_box"] = 0

        await self.save_bank_info(users)
        return True

    async def validation_check_mark(self, ctx, message):

        """
            Permet d'envoyer un message et d'attendre une reaction de l'utilisateur
            Renvoie un BOOLEAN
        """

        check_mark = "✔"
        cross_mark = "❌"

        # Permet de verifier si la reaction vient de l'autheur de la commande.
        def check_reaction(reaction, user):
            return ctx.message.author == user and message.id == reaction.message.id \
                   and (str(reaction.emoji) == check_mark or str(reaction.emoji) == cross_mark)

        message = await ctx.send(message)

        await message.add_reaction(check_mark)
        await message.add_reaction(cross_mark)

        try:
            target_reaction, target_user = await self.wait_for("reaction_add", timeout=10, check=check_reaction)
        except:
            await ctx.send("You didn't react quickly enough.")
            return False

        if target_reaction.emoji == check_mark:
            return True
        else:
            return False

    async def check_safe_deposit_amount(self, ctx, author_id, users, user_bet):

        # Ensuite on verifie si son compte n'est pas a 0$
        if await self.does_amount_equals_zero(author_id, users):
            await ctx.send("```diff\n- CANNOT ACTION: Your account limit is $ 0.```")
            return False

        # Ou qu'il possede suffisament d'argent pour en donner
        elif users[str(author_id)]["safe_deposit_box"] < int(user_bet):
            await ctx.send("```diff\n- IMPOSSIBLE ACTION: The limit of your account is lower "
                           "than the amount of the donation.```")
            return False

        else:
            return True

    async def check_user_answer(self, ctx):

        def check_message(message):
            return message.author == ctx.message.author and ctx.message.channel == message.channel

        try:
            answer = await self.wait_for("message", timeout=20, check=check_message)
        except:
            await ctx.send("Vous avez mis trop de temps. La roulette tourne deja.")
            return False

        answer_content = int(answer.content)
        users = await self.get_bank_info()

        if (await self.check_safe_deposit_amount(ctx, ctx.author.id, users, answer_content)) or \
                (0 >= answer_content or answer_content <= 37):
            return answer_content
        else:
            return False

    def add_commands(self):

        """
            Possede toutes les commandes utilisables par le bot
        """

        @self.command(name="roulette")
        async def roulette(ctx):

            """
                Permet de jouer au casino et ainsi gagner des sous. Le joueur choisi un chiffre entre 1 et 37
                Puis l'ordinateur tire aleatoirement un chiffre lui aussi entre 1 et 37. Si les chiffres correspondent
                alors le joueur gagne.
                Renvoie un BOOLEAN
            """

            await ctx.send("Welcome to roulette magic. The rules are simple you bet on a number, "
                           "If the ball lands on this number you win your bet x1.5. If you choose"
                           "the 0 and you win, you win your bet x4.")

            await ctx.send("Choisissez une somme a miser : ")

            # Permet la verification de la reponse du joueur ( si son compte possede assez de sous etc )
            player_bet = await self.check_user_answer(ctx)
            users = await self.get_bank_info()

            # Verifie si les bons check mark ont ete enclenche ( renvoie true ou false )
            if await self.validation_check_mark(ctx, "Do you want to validate your bet ?"):

                print("OK")

                if await self.check_safe_deposit_amount(ctx, ctx.author.id, users, player_bet):

                    print("OK")

                    await ctx.send("Placez votre mise ( entre 0 et 37 ) : ")

                    player_number = await self.check_user_answer(ctx)

                    random_number = random.randrange(37)

                    if random_number == 0:
                        bet_multiplier = 4
                    else:
                        bet_multiplier = 1.5

                    if player_number == random_number:

                        player_bet_final = player_bet*bet_multiplier

                        users[str(ctx.author.id)]["safe_deposit_box"] += player_bet_final

                        await self.save_bank_info(users)

                        em = discord.Embed(title="Roulette Magic", color=discord.Colour.random())
                        em.add_field(name="The ball stops on the square : ", value=str(random_number), inline=False)
                        em.add_field(name="You've earned :", value=str(player_bet_final), inline=True)

                        await ctx.send(embed=em)
                    else:
                        users[str(ctx.author.id)]["safe_deposit_box"] -= player_bet

                        em = discord.Embed(title="Roulette Magic", color=discord.Colour.random())
                        em.add_field(name="The ball stops on the square : ", value=str(random_number), inline=False)
                        em.add_field(name="You've lost :", value=str(player_bet), inline=True)

                        await ctx.send(embed=em)

                        await self.save_bank_info(users)
                        return False
                else:
                    await ctx.send("Vous n'avez pas la somme mise. Vous partez de la table.")
                    return False

            else:
                await ctx.send("You exit the gaming table.")
                return False

        @self.command(name="donate")
        async def donate(ctx, target_user: discord.User, donate_amount):

            """
                Permet aux utilisateur de se faire des dons entre eux.
                Renvoie un BOOLEAN dans certaines conditions
            """

            author_id = ctx.author.id

            users = await self.get_bank_info()

            # On verifie si l'autheur de la commande possede un compte
            if await self.does_user_has_account(author_id, users):

                # Ensuite on verifie si son compte n'est pas a 0$
                if await self.does_amount_equals_zero(author_id, users):
                    await ctx.send("```diff\n- CANNOT ACTION: Your account limit is $ 0.```")
                    return False

                # Ou qu'il possede suffisament d'argent pour en donner
                elif users[str(author_id)]["safe_deposit_box"] < int(donate_amount):
                    await ctx.send("```diff\n- IMPOSSIBLE ACTION: The limit of your account is lower "
                                   "than the amount of the donation.```")
                    return False

                else:
                    # Verification si la cible possede un compte / ouverture du compte si besoin
                    users[str(target_user.id)] = {}
                    users[str(target_user.id)]["safe_deposit_box"] = 0

                    # Recuperation des sous sur le compte de l'auheur
                    users[str(author_id)]["safe_deposit_box"] -= int(donate_amount)

                    # Ajout des sous sur le compte cible
                    users[str(target_user.id)]["safe_deposit_box"] += int(donate_amount)

                    await self.save_bank_info(users)

                    em = discord.Embed(title="Donate order", colour=discord.Colour.random())
                    em.add_field(name="Donation information", value=f"The donation of {donate_amount} $ "
                                                                    f"from {ctx.author.name} to {target_user.name} "
                                                                    f"is a success")

                    await ctx.send(embed=em)
                    print("OK")

            else:

                await ctx.send("```diff\n- CANNOT ACTION: you do not have an account.```")
                await ctx.send("```css\nCREATION OF AN ACCOUNT.```")
                await self.open_account(ctx.author)
                await ctx.send(f"```css\nCREATED ACCOUNT: Your limit is "
                               f"{users[str(ctx.author)]['safe_deposit_box']} $```")

        @self.command(name="beg")
        async def beg(ctx):

            """
                Permet de mendier des sous et ainsi gagner une somme entre 1 et 100
            """

            gain = random.randrange(101)

            # Recuperation des donnes du fichier JSON
            users = await self.get_bank_info()

            users[str(ctx.author.id)]["safe_deposit_box"] += gain  # Ajout du gain sur le compte du joueur

            await self.save_bank_info(users)

            await ctx.send(f"Someone gave you {gain} $")

        @self.command(name="balance")
        async def balance(ctx):

            """
                Permet de regarder le montant de son compte
            """

            await self.open_account(ctx.author)

            users = await self.get_bank_info()

            u_safe_deposit_amount = users[str(ctx.author.id)]["safe_deposit_box"]

            em = discord.Embed(title=f"{ctx.author.name}'s balance", colour=discord.Colour.random())
            em.add_field(name="Safe deposit box amount", value=f"{u_safe_deposit_amount} $", inline=True)

            await ctx.send(embed=em)


def run():
    print("Lancement du bot")
    client = MyClient()
    client.run(os.getenv("TOKEN"))
